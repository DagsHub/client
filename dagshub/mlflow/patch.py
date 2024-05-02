import inspect
import logging
import sys
import traceback
from types import ModuleType, FunctionType
from typing import Callable, Optional, Dict, Set

from tenacity import Retrying, stop_after_delay

logger = logging.getLogger(__name__)


class MlflowMonkeyPatch:
    context_manager_functions = ["start_run"]
    classes_to_patch = ["mlflow.tracking.client.MlflowClient"]

    def __init__(self):
        self.original_func_lookup: Dict[str, Callable] = {}
        self.patched_modules: Set[str] = set()

    def _wrap_func(self, fn: Callable) -> Callable:
        from mlflow.exceptions import MlflowException

        def is_top_level_mlflow_call() -> bool:
            tb = traceback.extract_stack()

            # Count the times `wrap_fn` function shows up in the stack trace,
            # if it's only once - means it's the top level mlflow call

            wrap_fn_met = False
            for stack_line in tb:
                is_wrap_func = stack_line.filename == __file__ and stack_line.name in [
                    "wrap_fn",
                    "context_manager_wrap_fn",
                ]
                if not is_wrap_func:
                    continue
                elif wrap_fn_met:
                    return False
                else:
                    wrap_fn_met = True

            return True

        def wrap_fn(*args, **kwargs):
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

        def context_manager_wrap_fn(*args, **kwargs):
            # Context managers (start_run), always return a value, so those we retry for a long amount of time instead
            # Swallowing this function's exception would break any call after that
            # Alternative might be returning a mock object that no-ops any calls to it
            for attempt in Retrying(stop=stop_after_delay(60 * 15), reraise=True):
                with attempt:
                    return fn(*args, **kwargs)

        if fn.__name__ in self.context_manager_functions:
            return context_manager_wrap_fn
        else:
            return wrap_fn

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
                if self.is_function_already_patched(full_attr_name):
                    continue
                self.original_func_lookup[full_attr_name] = attr
                setattr(module, attr_name, self._wrap_func(attr))
                continue

            if is_class and full_attr_name in self.classes_to_patch:
                for class_attr_name in dir(attr):
                    if class_attr_name.startswith("_"):
                        continue
                    class_attr = getattr(attr, class_attr_name)
                    full_class_attr_name = f"{full_attr_name}.{class_attr_name}"
                    if isinstance(class_attr, FunctionType) and not self.is_function_already_patched(
                        full_class_attr_name
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
        global _global_mlflow_patch

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
        _global_mlflow_patch = None


_global_mlflow_patch: Optional[MlflowMonkeyPatch] = None


def patch_mlflow():
    import mlflow

    global _global_mlflow_patch

    if _global_mlflow_patch is not None:
        logger.warning("MLflow is already patched")
        return

    logger.warning(
        "Patching MLflow to prevent any MLflow exceptions from being raised. "
        "Call dagshub.mlflow.unpatch_mlflow() to undo"
    )

    patch = MlflowMonkeyPatch()
    patch.monkey_patch_module(mlflow)
    _global_mlflow_patch = patch


def unpatch_mlflow():
    if _global_mlflow_patch is None:
        logger.warning("MLflow should be unpatched already")
        return
    _global_mlflow_patch.unpatch()
