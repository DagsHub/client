import dagshub

# A basic use case
repo = dagshub.Repo("idonov8", "baby-yoda-segmentation-dataset")
ds = repo.directory(".")

# with open("test_photo.png", 'rb') as f:
# 	ds.add(file=f, path="images") 
# 	ds.commit("Add a photo with the api", versioning="dvc")

# path is a full path, including the file name.	
ds.add(file="test_photo.png", path="images/my_awesome_image.png")
ds.commit("Add a photo with the api", versioning="dvc")