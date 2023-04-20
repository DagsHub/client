import logging
import os
import random
from typing import List

import IPython
import dacite
import httpx
import fiftyone as fo
import requests

import dagshub
from dagshub.auth.token_auth import HTTPBearerAuth
from dagshub.common import config
from dagshub.data_engine.model import datasources
from dagshub.streaming.dataclasses import ContentAPIEntry

logger = logging.getLogger(__name__)

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

    def create_datasource(self):
        logger.info("Creating datasource...")
        self.dataset.source.create()

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
        logger.info("Adding files")

        # Download random words for keys
        word_site = "https://www.mit.edu/~ecprice/wordlist.10000"
        response = requests.get(word_site)
        WORDS = response.content.decode("utf-8").splitlines()

        with self.dataset.metadata_context() as ctx:
            for entry in entries:
                filename = entry.path.split("/")[-1]
                img_num = int(filename.removesuffix(".png"))
                episode_num = img_num % 10 + 1

                meta_dict = {
                    "episode": episode_num
                }
                for i in range(15):
                    key = f"key_{random.randint(1, 10)}"
                    val = random.choice(WORDS)
                    meta_dict[key] = val

                ctx.update_metadata(entry.download_url, meta_dict)

    def make_voxel(self):
        logger.info("Importing to voxel51")
        v51_ds = self.dataset.and_query(episode_eq=1).or_query(episode_ge=5).to_voxel51_dataset()
        sess = fo.launch_app(v51_ds)
        IPython.embed()
        sess.wait()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    snippet_driver = DESnippetDriver()

    # TO CREATE DATASOURCE (If it wasn't yet)
    snippet_driver.create_datasource()

    # TO ADD FILES WITH METADATA. DO NOT REPEAT!!
    files = snippet_driver.get_file_list("images")
    snippet_driver.add_files_with_metadata(files)

    # QUERY TEST
    # snippet_driver.query()

    # TO CREATE THE VOXEL APP
    snippet_driver.make_voxel()
