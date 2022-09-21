import dagshub

# Simon's idea of it:
repo = dagshub.Repo("owner", "repo-name", "authToken")
ds = repo.directory("path/to/ds")
# if not ds.exists() -> ds.create() // for now, throw exeption

# Directory either exists or will be created
# print(ds.exists())
# "True" or "False"
with open("/Users/idonov/Code/Work/GitHub/streaming-client-1/upload-wrapper/floorplan.png") as f:
    ds.add(file=f, path="rel/path")
ds.commit("Add a photo", versioning="dvc", new_branch="new-branch")

# for f in files:
#     ds.add(file=f, path="rel/path")