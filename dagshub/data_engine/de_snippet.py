from dagshub.data_engine.model import datasources

def do_stuff():
    ds = datasources.from_bucket("kirill/cool-repo", "s3://hello")
    res = ds.peek()
    print(res)



if __name__ == "__main__":
    do_stuff()
