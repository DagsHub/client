from pathlib import PosixPath

import pytest

from dagshub.models.model_loaders import RepoModelLoader, BucketModelLoader, DagsHubStorageModelLoader
from dagshub.models.model_locator import ModelLocator, ModelNotFoundError


def test_not_found_in_empty_repo(locator, repo_mock):
    with pytest.raises(ModelNotFoundError):
        locator.find_model()


@pytest.mark.parametrize("dir_path", ["model", "models"])
def test_found_in_repo(locator, repo_with_repo_model):
    _, model_path = repo_with_repo_model
    loader = locator.find_model()
    assert isinstance(loader, RepoModelLoader)
    assert loader.path == model_path


@pytest.mark.parametrize("dir_path", ["model", "models"])
def test_found_in_dagshub_storage(locator, repo_with_dh_storage_model):
    _, model_path = repo_with_dh_storage_model
    loader = locator.find_model()
    assert isinstance(loader, DagsHubStorageModelLoader)
    assert loader.path == model_path


def test_found_in_yaml_repo(repo_with_yaml_repo_model, locator):
    _, model_dir = repo_with_yaml_repo_model
    loader = locator.find_model()
    assert isinstance(loader, RepoModelLoader)
    assert loader.path == model_dir


def test_found_in_yaml_storage(repo_with_yaml_bucket_model, locator):
    _, model_dir = repo_with_yaml_bucket_model
    loader = locator.find_model()
    assert isinstance(loader, BucketModelLoader)
    assert loader.path == model_dir


def test_found_in_yaml_dh_storage(repo_with_yaml_dh_storage_model, locator):
    _, model_dir = repo_with_yaml_dh_storage_model
    loader = locator.find_model()
    assert isinstance(loader, DagsHubStorageModelLoader)
    assert loader.path == model_dir


def test_found_when_passed_path(repo_mock):
    dir_path = "some/random/dir"
    repo_mock.add_repo_contents("", dirs=[dir_path])
    repo_mock.add_repo_file(f"{dir_path}/model.pt", b"blablabla")
    locator = ModelLocator(repo_mock, path=dir_path)
    loader = locator.find_model()
    assert isinstance(loader, RepoModelLoader)
    assert loader.path == PosixPath(dir_path)


def test_found_when_passed_bucket_root_as_path(repo_mock):
    bucket_name = "some-bucket/random/prefix"
    repo_mock.add_storage("s3", bucket_name)
    repo_mock.add_storage_file(f"s3/{bucket_name}/model.pt", b"blablabla")
    locator = ModelLocator(repo_mock, path=bucket_name)
    loader = locator.find_model()
    assert isinstance(loader, BucketModelLoader)
    assert loader.path == PosixPath(f"s3/{bucket_name}")


def test_raises_when_passed_path_and_not_found(repo_with_repo_model):
    # The existing model should be ignored
    repo_mock, _ = repo_with_repo_model

    dir_path = "some/random/dir"
    locator = ModelLocator(repo_mock, path=dir_path)
    with pytest.raises(ModelNotFoundError):
        locator.find_model()


def test_found_when_passed_bucket(repo_with_bucket_model, bucket_name):
    repo_mock, model_path = repo_with_bucket_model
    locator = ModelLocator(repo_mock, bucket=bucket_name)
    loader = locator.find_model()
    assert isinstance(loader, BucketModelLoader)
    assert loader.path == model_path


def test_raises_when_passed_bucket_and_not_found(repo_with_repo_model):
    # The existing model should be ignored
    repo_mock, _ = repo_with_repo_model

    protocol = "s3"
    bucket_name = "my-repo-bucket/random/prefix"

    repo_mock.add_storage(protocol, bucket_name)

    locator = ModelLocator(repo_mock, bucket=bucket_name)
    with pytest.raises(ModelNotFoundError):
        locator.find_model()
