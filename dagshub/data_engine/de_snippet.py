import logging
import os
from typing import List

import IPython
import dacite
import httpx
import fiftyone as fo

import dagshub
from dagshub.auth.token_auth import HTTPBearerAuth
from dagshub.common import config
from dagshub.data_engine.model import datasources
from dagshub.streaming.dataclasses import ContentAPIEntry


class DESnippetDriver:

    def __init__(self, repo="kirill/DataEngineTesting", bucket_url="s3://dagshub-storage"):
        self.repo = repo
        self.bucket_url = bucket_url
        self.dataset = self.init_dataset()
        self.host = config.host
        auth = HTTPBearerAuth(dagshub.auth.get_token(host=self.host))
        self.client = httpx.Client(auth=auth)

    def init_dataset(self):
        return datasources.from_bucket("my-data", self.repo, self.bucket_url)

    # def create_datasource(self):
    #     # TODO: make prettier actually :)
    #     self.dataset.source.client.create_datasource("Test-bucket", self.bucket_url)

    # def add_metadata(self):
    #     files = ["file1", "file2"]
    #     with self.dataset.metadata_context() as ctx:
    #         ctx.update_metadata(files, {"episode": 2})
    #
    # def add_more_metadata(self):
    #     with self.dataset.metadata_context() as ctx:
    #         ctx.update_metadata("file1", {"air_date": "2022-01-01"})
    #         ctx.update_metadata("file2", {"air_date": "2022-01-08"})
    #         ctx.update_metadata("file1", {"has_baby_yoda": True})

    def query(self):
        res = self.dataset.and_query(img_number_ge=5).or_query(img_number_eq=0).peek()
        # res = ds.or_query(episode_eq=2).peek()
        print(res.dataframe)

    def get_file_list(self, path):
        resp = self.client.get(self.dataset.source.content_path(path))
        return [dacite.from_dict(ContentAPIEntry, e) for e in resp.json()]

    def add_files_with_metadata(self, entries: List[ContentAPIEntry]):
        with self.dataset.metadata_context() as ctx:
            for index, entry in enumerate(entries):
                ctx.update_metadata(entry.download_url, {"img_number": index})

    def make_voxel(self):
        v51_ds = self.dataset.and_query(img_number_ge=5).or_query(img_number_eq=0).to_voxel51_dataset()
        sess = fo.launch_app(v51_ds)
        IPython.embed()
        sess.wait()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    snippet_driver = DESnippetDriver()
    files = snippet_driver.get_file_list("images")
    # TO ADD METADATA. DO NOT REPEAT!!
    # snippet_driver.add_files_with_metadata(files)

    # QUERY TEST
    # snippet_driver.query()

    # TO CREATE THE VOXEL APP
    snippet_driver.make_voxel()
