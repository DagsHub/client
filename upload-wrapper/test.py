import dagshub

# Simon's idea of it:
repo = dagshub.Repo("idonov8", "test-all-file-kinds")
ds = repo.directory("path/to/ds")
# if not ds.exists() -> ds.create() // for now, throw exeption

# Directory either exists or will be created
# print(ds.exists())
# "True" or "False"
with open("test_photo.png", 'rb') as f:
	ds.add(file=f, path="new_folder")
	ds.commit("Add a photo", versioning="dvc")

# for f in files:
#     ds.add(file=f, path="rel/path")