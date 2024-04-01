from abc import abstractmethod
from pathlib import Path, PurePosixPath
from typing import Literal, Optional

from dagshub.common.api import RepoAPI
from dagshub.common.helpers import log_message
from dagshub.streaming import DagsHubFilesystem


class ModelLoader:
    def __init__(self, repo_api: RepoAPI):
        self.repo_api = repo_api

    def load_model(
        self,
        mode: Literal["eager", "lazy"],
        download_dest: Path,
        revision: Optional[str] = None,
    ) -> Path:
        if mode == "eager":
            return self._eager_load(download_dest)
        elif mode == "lazy":
            if revision is None:
                revision = self.repo_api.default_branch
            return self._lazy_load(download_dest, revision)
        raise RuntimeError(f"Unknown model load mode [{mode}]")

    @abstractmethod
    def _eager_load(self, download_dest: Path) -> Path: ...

    def _lazy_load(self, download_dest: Path, revision: str) -> Path:
        fs = DagsHubFilesystem(
            project_root=download_dest,
            repo_url=self.repo_api.repo_url,
            branch=revision,
            frameworks=["transformers"],
        )
        res_path = download_dest / self.model_path
        log_message(
            f"Running install_hooks() in dir {download_dest}, "
            f"run dagshub.streaming.uninstall_hooks() if you want to run another model later"
        )
        fs.install_hooks()
        return res_path

    @property
    @abstractmethod
    def model_path(self) -> Path: ...


class RepoModelLoader(ModelLoader):
    def __init__(self, repo_api: RepoAPI, revision: str, path: PurePosixPath):
        super().__init__(repo_api)
        self.revision = revision
        self.path = path

    def load_model(
        self,
        mode: Literal["eager", "lazy"],
        download_dest: Path,
        revision: Optional[str] = None,
    ) -> Path:
        """Overrides the original to change the revision used. If it's not set, use the revision from the class"""
        if revision is None:
            revision = self.revision
        return super().load_model(mode, download_dest, revision)

    def _eager_load(self, download_dest: Path) -> Path:
        remote_path = self.path
        local_path = download_dest / self.model_path
        self.repo_api.download(
            remote_path, local_path=local_path, revision=self.revision
        )
        return local_path

    @property
    def model_path(self) -> Path:
        return Path(self.path)


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


class DagsHubStorageModelLoader(BucketModelLoader):
    def __init__(self, repo_api: RepoAPI, path: PurePosixPath):
        bucket_path = PurePosixPath("s3") / repo_api.repo_name / path
        super().__init__(repo_api, bucket_path)


class MLflowArtifactModelLoader(ModelLoader):
    def _eager_load(self, download_dest: Path) -> Path:
        raise NotImplementedError

    @property
    def model_path(self) -> Path:
        raise NotImplementedError
