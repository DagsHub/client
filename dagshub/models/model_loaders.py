from abc import abstractmethod
from pathlib import Path, PurePosixPath
from typing import Literal

from dagshub.common.api import RepoAPI
from dagshub.common.helpers import log_message
from dagshub.streaming import DagsHubFilesystem


class ModelLoader:
    def __init__(self, repo_api: RepoAPI):
        self.repo_api = repo_api

    def load_model(self, mode: Literal["eager", "lazy"], download_dest: Path) -> Path:
        if mode == "eager":
            return self._eager_load(download_dest)
        elif mode == "lazy":
            return self._lazy_load(download_dest)
        raise RuntimeError(f"Unknown model load mode [{mode}]")

    @abstractmethod
    def _eager_load(self, download_dest: Path) -> Path:
        ...

    def _lazy_load(self, download_dest: Path) -> Path:
        fs = DagsHubFilesystem(project_root=download_dest, repo_url=self.repo_api.repo_url)
        res_path = download_dest / self.model_path
        log_message(
            f"Running install_hooks() in dir {download_dest}, "
            f"run dagshub.streaming.uninstall_hooks() if you want to run another model later"
        )
        fs.install_hooks()
        return res_path

    @property
    @abstractmethod
    def model_path(self) -> Path:
        ...


class RepoModelLoader(ModelLoader):
    def __init__(self, repo_api: RepoAPI, revision: str, path: PurePosixPath):
        super().__init__(repo_api)
        self.revision = revision
        self.path = path

    def _eager_load(self, download_dest: Path) -> Path:
        remote_path = self.path
        local_path = download_dest / self.model_path
        self.repo_api.download(remote_path, local_path=local_path)
        return local_path

    @property
    def model_path(self) -> Path:
        return Path(self.path)


class DagsHubStorageModelLoader(ModelLoader):
    def __init__(self, repo_api: RepoAPI, path: PurePosixPath):
        super().__init__(repo_api)
        self.path = path

    def _eager_load(self, download_dest: Path) -> Path:
        remote_path = PurePosixPath(f"s3:/{self.repo_api.repo_name}") / self.path
        local_path = download_dest / self.model_path
        self.repo_api.download(remote_path, local_path=local_path)
        return local_path

    @property
    def model_path(self) -> Path:
        return Path(".dagshub") / "storage" / "s3" / self.repo_api.repo_name / self.path


class BucketModelLoader(ModelLoader):
    def __init__(self, repo_api: RepoAPI, path: PurePosixPath):
        super().__init__(repo_api)
        self.path = path

    def _eager_load(self, download_dest: Path) -> Path:
        # Need to change from s3/bucket/bla-bla to s3:/bucket/bla-bla for download to work
        remote_path = str(self.path).replace("/", ":/", 1)
        local_path = download_dest / self.model_path
        self.repo_api.download(remote_path, local_path=local_path)
        return local_path

    @property
    def model_path(self) -> Path:
        return Path(".dagshub") / "storage" / self.path


class MLflowArtifactModelLoader(ModelLoader):
    def _eager_load(self, download_dest: Path) -> Path:
        raise NotImplementedError

    def _lazy_load(self, download_dest: Path) -> Path:
        raise NotImplementedError

    @property
    def model_path(self) -> Path:
        raise NotImplementedError
