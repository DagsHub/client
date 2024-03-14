from functools import wraps


def wrapreturn(wrapper_type):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return wrapper_type(func(*args, **kwargs))

        return wrapper

    return decorator
