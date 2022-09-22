import dagshub

# A basic use case
repo = dagshub.Repo("idonov8", "test-all-file-kinds")
ds = repo.directory("path/to/ds")

with open("test_photo.png", 'rb') as f:
	# path is the enclosing folder, not including file name
	ds.add(file=f, path="new_folder") 
	ds.commit("Add a photo", versioning="dvc", new_branch="meow-2")

# # path is a full path, including the file name.	
# ds.add(file="files/my_file.txt", path="remote_files/my_file.txt")