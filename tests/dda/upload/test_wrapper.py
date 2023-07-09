import os
import tempfile
import uuid
from pathlib import Path

import pytest

from dagshub.upload import Repo
from tests.dda.mock_api import MockApi


@pytest.fixture
def test_file() -> str:
    filepath = f"{uuid.uuid4()}.txt"
    with open(filepath, "w") as f:
        f.write("test data")
    yield filepath
    try:
        os.remove(filepath)
    except (OSError, FileNotFoundError):
        pass


@pytest.fixture
def test_dirs() -> str:
    folder_path = Path("nested", "folder")
    folder_path.mkdir(exist_ok=True, parents=True)
    filepath1 = folder_path / f"{uuid.uuid4()}.txt"
    filepath1.write_text("test data")
    filepath2 = folder_path / f"{uuid.uuid4()}.txt"
    filepath2.write_text("test data")
    yield str(folder_path)
    try:
        os.remove(filepath1)
        os.remove(filepath2)
        os.removedirs(folder_path)
    except (OSError, FileNotFoundError):
        pass


@pytest.fixture
def temp_dir() -> str:
    with tempfile.TemporaryDirectory() as temp_dir:
        folder_path = Path(temp_dir) / "nested" / "foldername"
        folder_path.mkdir(parents=True, exist_ok=True)
        file_path = folder_path / "example_file.txt"
        file_path.write_text("This is an example file.")
        yield str(folder_path)


def test_upload_dataset_closes_files(mock_api: MockApi, upload_repo: Repo, test_file: str):
    ds = upload_repo.directory("subdir")
    file_handle = open(test_file)
    ds.add(file_handle, "filepath.txt")
    ds.commit()
    assert file_handle.closed


def test_upload_folder_preserves_relative_path(mock_api: MockApi, upload_repo: Repo, test_dirs: str):
    do_upload_folder_test(mock_api, test_dirs, "nested/folder", upload_repo)


def test_upload_folder_absolute_path_can_be_relative(mock_api: MockApi, upload_repo: Repo, test_dirs: str):
    abspath = os.path.abspath(test_dirs)
    do_upload_folder_test(mock_api, abspath, "nested/folder", upload_repo)


def test_upload_folder_absolute_path_outside_cwd(mock_api: MockApi, upload_repo: Repo, temp_dir: str):
    do_upload_folder_test(mock_api, temp_dir, "foldername", upload_repo)


def test_upload_folder_relative_path_outside_cwd(mock_api: MockApi, upload_repo: Repo, temp_dir: str):
    relpath = os.path.relpath(temp_dir, os.getcwd())
    assert relpath.startswith('..')
    do_upload_folder_test(mock_api, relpath, "foldername", upload_repo)


def do_upload_folder_test(mock_api: MockApi, src_dirs: str, dst_dirs: str, upload_repo: Repo):
    upload_repo.upload(local_path=src_dirs)
    upload_route = mock_api.routes['upload']
    upload_route.calls.assert_called_once()
    call = upload_route.calls.last
    assert call.response.status_code == 200
    assert call.request.method == 'PUT'
    expected = f'/api/v1/repos/{upload_repo.owner}/{upload_repo.name}/content/{upload_repo.branch}/{dst_dirs}'
    assert call.request.url.path == expected
