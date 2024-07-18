import os
from pathlib import Path
from typing import cast

import pytest

from dagshub.data_engine.annotation.importer import AnnotationImporter, AnnotationsNotFoundError
from dagshub.data_engine.model.datasource import Datasource
from tests.mocks.repo_api import MockRepoAPI
from tests.util import remember_cwd


@pytest.fixture
def annotation_ds(ds) -> Datasource:
    ds.source.path = "repo://kirill/repo:main/data/images"

    repoApi = cast(MockRepoAPI, ds.source.repoApi)
    repoApi.add_repo_file("data/labels/1.txt", b"1")

    return ds


def test_load_location_on_disk(annotation_ds, tmp_path):
    """Also tests that disk takes priority over repo."""
    with remember_cwd():
        os.chdir(tmp_path)
        Path("data/labels").mkdir(parents=True)
        Path("data/labels/1.txt").write_text("1")
        assert AnnotationImporter.determine_load_location(annotation_ds, "data/labels/1.txt") == "disk"


def test_load_location_on_repo(annotation_ds):
    assert AnnotationImporter.determine_load_location(annotation_ds, "data/labels/1.txt") == "repo"


def test_load_location_fails(annotation_ds):
    with pytest.raises(AnnotationsNotFoundError):
        AnnotationImporter.determine_load_location(annotation_ds, "random_path")
