import logging

from dagshub.data_engine.model import datasources

repo = "KBolashev/data-engine-test"
bucket_url = "s3://test"


def get_dataset():
    return datasources.from_bucket(repo, bucket_url)


def do_stuff():
    ds = get_dataset()
    new_ds = ds.and_query(name_eq="aaaa", has_squirrel_eq=True).or_query(img_size_gt=480)
    ds.and_query(**{"some-number_lt": 2}).peek()
    res = new_ds.peek()
    print(res)


def create_datasource():
    ds = get_dataset()
    # TODO: make prettier actually :)
    ds.source.client.create_datasource("Test-bucket", bucket_url)


def add_metadata():
    ds = get_dataset()
    files = ["file1", "file2"]
    with ds.metadata_context() as ctx:
        ctx.update_metadata(files, {"episode": 2})


def add_more_metadata():
    ds = get_dataset()
    with ds.metadata_context() as ctx:
        ctx.update_metadata("file1", {"air_date": "2022-01-01"})
        ctx.update_metadata("file2", {"air_date": "2022-01-08"})
        ctx.update_metadata("file1", {"has_baby_yoda": True})


def query():
    ds = get_dataset()
    # res = ds.and_query(episode_eq=2).or_query(filename_contains="a").peek()
    res = ds.or_query(episode_eq=2).peek()
    print(res.dataframe)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    query()
    # add_more_metadata()
    # add_metadata()
    # create_datasource()
    # do_stuff()
