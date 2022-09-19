# Simon's idea of it:
repo = dagshub.Repo("owner", "repo-name", authToken)
ds = repo.directory("path/to/ds")
# if not ds.exists() -> ds.create() // for now, throw exeption

# Directory either exists or will be created
# print(ds.exists())
# "True" or "False"
for f in files:
    ds.add(file=f, path="rel/path")
ds.commit("Add some files with git & dvc", versioning="auto")