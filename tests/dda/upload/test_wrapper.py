import os
import uuid

import pytest

from dagshub.upload import Repo


@pytest.fixture(scope="function")
def test_file():
    filepath = f"{uuid.uuid4()}.txt"
    with open(filepath, "w") as f:
        f.write("test data")
    yield filepath
    try:
        os.remove(filepath)
    except OSError:
        pass


def test_upload_dataset_closes_files(mock_api, upload_repo: Repo, test_file: str):
    ds = upload_repo.directory("subdir")
    file_handle = open(test_file)
    ds.add(file_handle, "filepath.txt")
    ds.commit()
    assert file_handle.closed
