from .filesystem import DagsHubFilesystem, install_hooks, uninstall_hooks

try:
    from .mount import mount
except ImportError as e:
    error = e.msg

    def mount(*args, **kwargs):
        print(error)

except OSError as e:
    error = e.strerror

    def mount(*args, **kwargs):
        print(error)


__all__ = [DagsHubFilesystem.__name__, install_hooks.__name__, mount.__name__, uninstall_hooks.__name__]
