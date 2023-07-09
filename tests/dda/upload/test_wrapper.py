import os
import tempfile
import uuid

import pytest

from dagshub.upload import Repo
from tests.dda.mock_api import MockApi


@pytest.fixture(scope="function")
def test_file() -> str:
    filepath = f"{uuid.uuid4()}.txt"
    with open(filepath, "w") as f:
        f.write("test data")
    yield filepath
    try:
        os.remove(filepath)
    except (OSError, FileNotFoundError):
        pass


@pytest.fixture(scope="function")
def test_dirs() -> str:
    folder_path = os.path.join("nested", "folder")
    os.makedirs(folder_path, exist_ok=True)

    filepath1 = os.path.join(folder_path, f"{uuid.uuid4()}.txt")
    with open(filepath1, "w") as f:
        f.write("test data")
    filepath2 = os.path.join(folder_path, f"{uuid.uuid4()}.txt")
    with open(filepath2, "w") as f:
        f.write("test data")

    yield folder_path
    try:
        os.remove(filepath1)
        os.remove(filepath2)
        os.removedirs(folder_path)
    except (OSError, FileNotFoundError):
        pass


@pytest.fixture(scope="function")
def temp_dir() -> str:
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Define the nested folder path
        folder_path = os.path.join(temp_dir, "nested", "foldername")

        # Create the nested folder
        os.makedirs(folder_path, exist_ok=True)

        file_path = os.path.join(folder_path, "example_file.txt")
        with open(file_path, "w") as file:
            file.write("This is an example file.")

        yield folder_path


def test_upload_dataset_closes_files(mock_api: MockApi, upload_repo: Repo, test_file: str):
    ds = upload_repo.directory("subdir")
    file_handle = open(test_file)
    ds.add(file_handle, "filepath.txt")
    ds.commit()
    assert file_handle.closed


def test_upload_folder_preserves_relative_path(mock_api: MockApi, upload_repo: Repo, test_dirs: str):
    do_upload_folder_test(mock_api, test_dirs, test_dirs, upload_repo)


def test_upload_folder_absolute_path_can_be_relative(mock_api: MockApi, upload_repo: Repo, test_dirs: str):
    abspath = os.path.abspath(test_dirs)
    do_upload_folder_test(mock_api, abspath, test_dirs, upload_repo)


def do_upload_folder_test(mock_api: MockApi, src_dirs: str, dst_dirs: str, upload_repo: Repo):
    upload_repo.upload(local_path=src_dirs)
    upload_route = mock_api.routes['upload']
    upload_route.calls.assert_called_once()
    call = upload_route.calls.last
    assert call.response.status_code == 200
    assert call.request.method == 'PUT'
    expected = f'/api/v1/repos/{upload_repo.owner}/{upload_repo.name}/content/{upload_repo.branch}/{dst_dirs}'
    assert call.request.url.path == expected


def test_upload_folder_absolute_path_outside_cwd(mock_api: MockApi, upload_repo: Repo, temp_dir: str):
    do_upload_folder_test(mock_api, temp_dir, "foldername", upload_repo)


def test_upload_folder_relative_path_outside_cwd(mock_api: MockApi, upload_repo: Repo, temp_dir: str):
    relpath = os.path.relpath(temp_dir, os.getcwd())
    assert relpath.startswith('..')
    do_upload_folder_test(mock_api, relpath, "foldername", upload_repo)
