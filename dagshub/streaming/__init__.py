from .filesystem import DagsHubFilesystem, install_hooks, uninstall_hooks


try:
    from .mount import mount, unmount
except ImportError as e:
    error = e.msg

    def mount(*args, **kwargs):
        print(error)

    def unmount():
        print(error)

__all__ = [
    DagsHubFilesystem.__name__,
    install_hooks.__name__,
    mount.__name__,
    uninstall_hooks.__name__,
    unmount.__name__
]
