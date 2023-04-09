from dagshub.data_engine.model import datasources

def do_stuff():
    ds = datasources.from_bucket("kirill/cool-repo", "s3://hello")
    new_ds = ds.and_query(name_eq="aaaa", has_squirrel_eq=True).or_query(img_size_gt=480)
    res = new_ds.peek()
    print(res)


if __name__ == "__main__":
    do_stuff()
