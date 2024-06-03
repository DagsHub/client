import inspect
import logging
import sys
import threading
import traceback
from types import ModuleType, FunctionType
from typing import Callable, Optional, Dict, Set, List, Tuple

from tenacity import Retrying, stop_after_delay

logger = logging.getLogger(__name__)

_top_level_functions = [
    "mlflow.log_artifact",
    "mlflow.log_artifacts",
    "mlflow.log_dict",
    "mlflow.log_figure",
    "mlflow.log_image",
    "mlflow.log_input",
    "mlflow.log_metric",
    "mlflow.log_metrics",
    "mlflow.log_param",
    "mlflow.log_params",
    "mlflow.log_table",
    "mlflow.log_text",
]

_mlflow_client_functions = [
    "mlflow.tracking.client.MlflowClient.log_artifact",
    "mlflow.tracking.client.MlflowClient.log_artifacts",
    "mlflow.tracking.client.MlflowClient.log_batch",
    "mlflow.tracking.client.MlflowClient.log_dict",
    "mlflow.tracking.client.MlflowClient.log_figure",
    "mlflow.tracking.client.MlflowClient.log_image",
    "mlflow.tracking.client.MlflowClient.log_inputs",
    "mlflow.tracking.client.MlflowClient.log_metric",
    "mlflow.tracking.client.MlflowClient.log_param",
    "mlflow.tracking.client.MlflowClient.log_table",
    "mlflow.tracking.client.MlflowClient.log_text",
]

_default_patch_functions = _top_level_functions + _mlflow_client_functions

_default_guaranteed_raises = ["log_model"]


class MlflowMonkeyPatch:
    context_manager_functions = ["start_run"]

    def __init__(self, funcs_to_patch: List[str], guaranteed_raises: List[str]):
        self.funcs_to_patch = set(funcs_to_patch)
        # Functions that guarantee to raise an exception if they are in the stack
        # Example: all mlflow.<framework>.log_model functions underneath use log_artifact,
        # but we might want to raise exceptions, so logging models doesn't get swallowed
        self.functions_with_guaranteed_raises = set(guaranteed_raises)

        self.original_func_lookup: Dict[str, Callable] = {}
        self.patched_modules: Set[str] = set()

    def _wrap_func(self, fn: Callable) -> Callable:
        from mlflow.exceptions import MlflowException

        def is_top_level_mlflow_call() -> bool:
            tb = traceback.extract_stack()

            # Count the times `dh_mlflow_wrap_fn` functions show up in the stack trace,
            # if it's only once - means it's the top-most level wrapped mlflow call

            wrap_fn_met = False
            for stack_line in tb:
                # If there is a guaranteed raise in the stack - return False
                if stack_line.name in self.functions_with_guaranteed_raises:
                    return False
                is_wrap_func = stack_line.filename == __file__ and stack_line.name in {
                    "dh_mlflow_wrap_fn",
                    "dh_mlflow_context_manager_wrap_fn",
                }
                if not is_wrap_func:
                    continue
                elif wrap_fn_met:
                    return False
                else:
                    wrap_fn_met = True

            return True

        def dh_mlflow_wrap_fn(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except MlflowException:
                # Allow exceptions to bubble up if it's not the top-level user made call
                if not is_top_level_mlflow_call():
                    raise
                logger.exception(
                    f"MlflowException occurred when calling {fn.__name__} "
                    f"but was suppressed due to running dagshub.mlflow.patch_mlflow:"
                )

        def dh_mlflow_context_manager_wrap_fn(*args, **kwargs):
            # Context managers (start_run), always return a value, so those we retry for a long amount of time instead
            # Swallowing this function's exception would break any call after that
            # Alternative might be returning a mock object that no-ops any calls to it
            for attempt in Retrying(stop=stop_after_delay(60 * 15), reraise=True):
                with attempt:
                    return fn(*args, **kwargs)

        if fn.__name__ in self.context_manager_functions:
            return dh_mlflow_context_manager_wrap_fn
        else:
            return dh_mlflow_wrap_fn

    def is_function_already_patched(self, func_name: str) -> bool:
        return func_name in self.original_func_lookup

    def monkey_patch_module(self, module: ModuleType):
        from mlflow.utils.lazy_load import LazyLoader

        # Add module into set of patched modules, so there's no circular import recursion
        self.patched_modules.add(module.__name__)

        # Traverses the module tree and monkey patches the accessible functions with wrap_func
        for attr_name in dir(module):
            # Skip dunder and private methods, bad idea to wrap them, we are only concerned with public-facing API
            if attr_name.startswith("_"):
                continue

            full_attr_name = f"{module.__name__}.{attr_name}"
            attr = getattr(module, attr_name)

            is_function = isinstance(attr, FunctionType)
            is_class = inspect.isclass(attr)

            if is_function:
                if full_attr_name not in self.funcs_to_patch:
                    continue
                if self.is_function_already_patched(full_attr_name):
                    continue
                self.original_func_lookup[full_attr_name] = attr
                setattr(module, attr_name, self._wrap_func(attr))
                continue

            if is_class:
                for class_attr_name in dir(attr):
                    if class_attr_name.startswith("_"):
                        continue
                    class_attr = getattr(attr, class_attr_name)
                    full_class_attr_name = f"{full_attr_name}.{class_attr_name}"
                    if (
                        isinstance(class_attr, FunctionType)
                        and not self.is_function_already_patched(full_class_attr_name)
                        and full_class_attr_name in self.funcs_to_patch
                    ):
                        self.original_func_lookup[full_class_attr_name] = class_attr
                        setattr(attr, class_attr_name, self._wrap_func(class_attr))

            is_module = isinstance(attr, ModuleType)
            # Ignore lazy loaded modules, don't want to load them all at once
            # TODO: maybe let users tune this somehow, although from what I've seen most of those are wrappers,
            #  and the actual mlflow logging functions are eagerly loaded
            is_lazy_module = isinstance(attr, LazyLoader)

            if not is_module or is_lazy_module:
                continue

            full_module_name = attr.__name__

            if not full_module_name.startswith("mlflow"):
                continue

            if full_module_name in self.patched_modules:
                continue

            # Recurse into the module and patch it
            self.monkey_patch_module(attr)

    def unpatch(self):
        logger.warning("Unpatching MLflow to raise exceptions again")

        for unpatched_key, unpatched_func in self.original_func_lookup.items():
            attrs = unpatched_key.split(".")
            module_name = attrs[0]
            attrs = attrs[1:]
            attr = sys.modules[module_name]
            for index, attr_name in enumerate(attrs):
                parent_attr = attr
                attr = getattr(parent_attr, attr_name)
                if index == len(attrs) - 1:
                    setattr(parent_attr, attr_name, unpatched_func)

        self.patched_modules.clear()
        self.original_func_lookup.clear()


_global_mlflow_patch: Optional[MlflowMonkeyPatch] = None
_patch_mutex = threading.Lock()


def _patch_mlflow(funcs_to_patch: List[str], guaranteed_raises: List[str]):
    import mlflow

    global _global_mlflow_patch

    with _patch_mutex:
        if _global_mlflow_patch is not None:
            logger.warning("MLflow is already patched")
            return

        logger.warning(
            "Patching MLflow to prevent any MLflow exceptions from being raised. "
            "Call dagshub.mlflow.unpatch_mlflow() to undo"
        )

        patch = MlflowMonkeyPatch(funcs_to_patch, guaranteed_raises)
        patch.monkey_patch_module(mlflow)
        _global_mlflow_patch = patch


def _resolve_patches(
    include: Optional[List[str]],
    exclude: Optional[List[str]],
    patch_top_level: bool,
    patch_mlflow_client: bool,
    raise_on_log_model: bool,
) -> Tuple[List[str], List[str]]:
    """
    Resolve the arguments for patch_mlflow

    Returns:
        Tuple of:
        - List of functions that need to be patched
        - List of functions that should raise exceptions if they are in the stack
    """
    funcs_to_patch = _default_patch_functions.copy()
    guaranteed_raises = _default_guaranteed_raises.copy()

    if not patch_top_level:
        for f in _top_level_functions:
            if f in funcs_to_patch:
                funcs_to_patch.remove(f)

    if not patch_mlflow_client:
        for f in _mlflow_client_functions:
            if f in funcs_to_patch:
                funcs_to_patch.remove(f)

    if include is not None:
        funcs_to_patch = funcs_to_patch + include

    if exclude is not None:
        for f in exclude:
            if f in funcs_to_patch:
                funcs_to_patch.remove(f)

    if not raise_on_log_model:
        if "log_model" in guaranteed_raises:
            guaranteed_raises.remove("log_model")

    return funcs_to_patch, guaranteed_raises


def patch_mlflow(
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    raise_on_log_model=True,
    patch_top_level=True,
    patch_mlflow_client=True,
):
    """
    Patch MLflow functions, making some of them stop raising exceptions, instead logging them to console.
    This is useful for long runs that have MLflow failing occasionally,
    so you don't have to restart the run if logging failed.

    By default, all top-level ``mlflow.log_...`` and ``MlflowClient.log_...`` functions are patched.

    Args:
        include: List of full names of functions you want to patch additionally to the default ones.
        exclude: List of functions you DON'T want to patch.\
            Use this if you need to make sure, for example, all ``log_artifact``
            functions raise an exception on failure:

            .. code-block:: python

                patch_mlflow(exclude=["mlflow.log_artifact", "mlflow.log_artifacts"])

        raise_on_log_model: If ``True``, patched log calls still raise an exception
            if they are called from a ``log_model`` function.

            This ensures that even if you want to ignore failed calls to ``log_artifact`` or ``log_figure`` etc.,
            failed calls to ``log_model`` in particular will still raise errors.
            This should work for all supported ML frameworks, as long as the function is named ``log_model``.
        patch_top_level: Whether to patch the top level ``mlflow`` functions.
        patch_mlflow_client: Whether to patch the ``MlflowClient`` class.
    """
    funcs_to_patch, guaranteed_raises = _resolve_patches(
        include=include,
        exclude=exclude,
        patch_top_level=patch_top_level,
        patch_mlflow_client=patch_mlflow_client,
        raise_on_log_model=raise_on_log_model,
    )

    _patch_mlflow(funcs_to_patch, guaranteed_raises)


def unpatch_mlflow():
    """
    Removes the failsafe MLflow patching, returning all MLflow functions to their original state
    """
    global _global_mlflow_patch

    with _patch_mutex:
        if _global_mlflow_patch is None:
            logger.warning("MLflow should be unpatched already")
            return
        _global_mlflow_patch.unpatch()
        _global_mlflow_patch = None


# TODO: add a "with_unpatch" (name subject to change) context manager, that disables the patching
# Implementation: set a THREAD LOCAL flag that disables the wrapping behaviour inside of the functions
