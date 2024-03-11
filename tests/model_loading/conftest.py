from pathlib import PurePosixPath
from typing import Tuple

import pytest

from dagshub.models.model_locator import ModelLocator
from tests.mocks.repo_api import MockRepoAPI


@pytest.fixture
def repo_user():
    return "user"


@pytest.fixture
def repo_name():
    return "repo"


@pytest.fixture
def repo_mock(repo_user, repo_name):
    mock = MockRepoAPI(f"{repo_user}/{repo_name}")
    return mock


@pytest.fixture
def locator(repo_mock):
    return ModelLocator(repo_mock)


@pytest.fixture
def repo_with_yaml_repo_model(repo_mock) -> Tuple[MockRepoAPI, PurePosixPath]:
    model_dir = "random/dir"
    yaml_content = f'model_dir: "{model_dir}"'.encode("utf-8")
    repo_mock.add_repo_file(".dagshub/model.yaml", yaml_content)

    repo_mock.add_repo_contents("", dirs=[model_dir])
    repo_mock.add_repo_file(f"{model_dir}/model.pt", b"blablabla")
    return repo_mock, PurePosixPath(model_dir)


@pytest.fixture
def repo_with_yaml_dh_storage_model(repo_mock) -> Tuple[MockRepoAPI, PurePosixPath]:
    model_dir = "dir"
    yaml_content = f'model_dir: "dagshub_storage/{model_dir}"'.encode("utf-8")
    repo_mock.add_repo_file(".dagshub/model.yaml", yaml_content)

    repo_mock.add_dagshub_storage_contents("", dirs=[model_dir])
    repo_mock.add_dagshub_storage_file(f"{model_dir}/model.pt", b"blablabla")
    return repo_mock, PurePosixPath(model_dir)


@pytest.fixture
def repo_with_yaml_bucket_model(repo_mock, bucket_name, protocol) -> Tuple[MockRepoAPI, PurePosixPath]:
    repo_mock.add_storage(protocol, bucket_name)

    full_bucket_name = f"{protocol}/{bucket_name}"

    model_dir = "dir"
    yaml_content = f'model_dir: "{bucket_name}/{model_dir}"'.encode("utf-8")
    repo_mock.add_repo_file(".dagshub/model.yaml", yaml_content)

    repo_mock.add_storage_contents(full_bucket_name, dirs=[model_dir])
    repo_mock.add_storage_file(f"{full_bucket_name}/{model_dir}/model.pt", b"blablabla")
    return repo_mock, PurePosixPath(f"{full_bucket_name}/{model_dir}")


@pytest.fixture
def repo_with_dh_storage_model(repo_mock, dir_path) -> Tuple[MockRepoAPI, PurePosixPath]:
    repo_mock.add_dagshub_storage_contents("", dirs=[dir_path])
    repo_mock.add_dagshub_storage_file(f"{dir_path}/model.pt", b"blablabla")
    return repo_mock, PurePosixPath(f"{dir_path}")


@pytest.fixture
def repo_with_repo_model(repo_mock, dir_path) -> Tuple[MockRepoAPI, PurePosixPath]:
    repo_mock.add_repo_contents("", dirs=[dir_path])
    repo_mock.add_repo_file(f"{dir_path}/model.pt", b"blablabla")
    return repo_mock, PurePosixPath(dir_path)


@pytest.fixture
def bucket_name():
    return "my-bucket/prefix"


@pytest.fixture(params=["model", "models"])
def dir_path(request):
    return request.param


@pytest.fixture(params=["s3", "gs", "azure"])
def protocol(request):
    return request.param


@pytest.fixture
def repo_with_bucket_model(repo_mock, dir_path, protocol, bucket_name) -> Tuple[MockRepoAPI, PurePosixPath]:
    repo_mock.add_storage(protocol, bucket_name)
    full_bucket_name = f"{protocol}/{bucket_name}"
    repo_mock.add_storage_contents(full_bucket_name, dirs=[dir_path])
    repo_mock.add_storage_file(f"{full_bucket_name}/{dir_path}/model.pt", b"blablabla")
    return repo_mock, PurePosixPath(f"{full_bucket_name}/{dir_path}")
