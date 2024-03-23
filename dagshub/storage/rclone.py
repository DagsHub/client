import subprocess
import configparser
import os
from pathlib import Path
from dagshub.auth import get_token


def check_and_provide_install_script():
    """
    Checks whether Rclone and fuse3 are installed on the system. If not, it provides the necessary
    installation commands.

    No parameters are required for this function.
    """
    packages = {
        "rclone": "sudo -v && curl https://rclone.org/install.sh | sudo bash",
        "fusermount3": "apt install -y fuse3"
    }
    install_commands = []

    for package, install_command in packages.items():
        try:
            # Check if the package is installed by querying its version
            subprocess.run([package, "--version"],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           text=True,
                           check=True)
            print(f"{package} is installed.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            # If not installed, add the install command to the list
            install_commands.append(install_command)

    if install_commands:
        # If there are packages to install, print the combined install commands
        print("Some packages are not installed. To install them, run the following commands:")
        for cmd in install_commands:
            print(f"!{cmd}")
    else:
        print("All packages are installed.")


def rclone_init(repo_owner: str, conf_path: Path = None, update=False, verbose=True) -> Path:
    """
    Initializes or updates the Rclone configuration for a DAGsHub repository.

    :param repo_owner: The owner of the repository. This is used to create a unique section in the Rclone configuration.
    :param conf_path: Optional. The path to the Rclone configuration file. If not provided, the default path is used.
    :param update: Optional. A boolean flag indicating whether to update the configuration if it already exists.
    Defaults to False.
    :param verbose: Optional. A boolean flag that controls the output of the function. If True, the function will
    print messages about its operation.
    :return: The absolute path to the Rclone configuration file.
    """
    # Make sure RClone and fuse3 are properly installed
    check_and_provide_install_script()

    if conf_path is None:
        root_path = Path.home() / ".config/rclone/"
        conf_path = root_path / "rclone.conf"
        if not os.path.exists(root_path):
            os.makedirs(Path.home() / ".config/rclone/")
    else:
        conf_path = Path(conf_path)

    token = get_token()

    config = configparser.ConfigParser()
    if conf_path.exists():
        config.read(conf_path)

    # Determine the section name
    if "dagshub" in config and not update:
        section_name = f"dagshub-{repo_owner}"
    else:
        section_name = "dagshub"

    config[section_name] = {
        "type": "s3",
        "provider": "Other",
        "access_key_id": token,
        "secret_access_key": token,
        "endpoint": f"https://dagshub.com/api/v1/repo-buckets/s3/{repo_owner}",
    }

    with conf_path.open("w") as f:
        config.write(f)

    if verbose:
        # Inform the user about the remote name
        print(f"Configuration complete. The remote '{section_name}' has been created/updated in '{conf_path}'.")
        print(f"Example usage with rclone: `rclone ls {section_name}:<your-bucket-name>` to list the contents of "
              f"'your-bucket-name'.")

    return conf_path.absolute()


def mount_bucket(repo: str, cache: bool = False, path: Path = None):
    """
    Mounts a DAGsHub repository bucket to a local directory.

    Note: This function is only supported on Linux machines and on macOS via FUSE for macOS (FUSE-T or macFUSE).
    It may not work as expected on other operating systems due to differences in the handling of filesystem mounts.

    :param repo: The repository in the format "<repo_owner>/<repo_name>". This is used to determine the remote name and
    mount point.
    :param cache: Optional. A boolean flag that enables or disables the cache feature. If True, caching is enabled with
    specific settings.
    :param path: Optional. A Path object specifying the custom mount path. If not provided, the mount directory is
    determined based on the current working directory and the repository name.
    """
    # Parse the repo string to get the repo owner and name
    repo_owner, repo_name = repo.split('/')

    # Determine the mount directory
    if path is not None:
        mount_dir = Path(path)
    else:
        current_dir = Path(os.getcwd()).name
        if current_dir == repo_name:
            mount_dir = Path("dagshub_storage")
        else:
            mount_dir = Path(repo_name) / "dagshub_storage"

    # 2. Configure the rclone conf
    conf_path = rclone_init(repo_owner=repo_owner, verbose=False)
    if not conf_path or not conf_path.exists():
        print("Failed to configure rclone.")
        return

    # 3. Prepare and execute the mount command
    mount_dir.mkdir(parents=True, exist_ok=True)
    mount_command = [
        "rclone", "mount", "--daemon", "--allow-other", "--vfs-cache-mode", "full",
        f"dagshub:{repo_name}/", f"{mount_dir}/"
    ]

    # Add cache options if needed
    if cache:
        mount_command.extend(["--vfs-cache-max-age", "24h"])

    try:
        # Execute the mount command
        subprocess.run(mount_command, check=True)
        print(f"Successfully mounted '{repo_name}' to '{mount_dir}'.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to mount '{repo_name}': {e}")


def unmount_bucket(repo_name, path=None):
    """
    Unmounts a previously mounted DAGsHub repository bucket from the local file system.

    :param repo_name: The name of the repository. Used to determine the default mount point if a custom path is
    not provided.
    :param path: Optional. A custom path to the mount point. If not provided, the default logic is used to determine
    the mount point based on the repository name.
    """
    if path:
        # If a custom path is provided, use it as the mount point
        mount_point = Path(path)
    else:
        # Default logic to determine the mount point
        current_dir = Path(os.getcwd()).name
        if current_dir == repo_name:
            mount_point = Path("dagshub_storage")
        else:
            mount_point = Path(repo_name) / "dagshub_storage"

    if mount_point.exists() and mount_point.is_dir():
        try:
            subprocess.run(['fusermount', '-u', str(mount_point)], check=True)
            print(f"Successfully unmounted '{mount_point}'.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to unmount '{mount_point}': {e}")
    else:
        print(f"Mount point '{mount_point}' does not exist or is not a directory.")
