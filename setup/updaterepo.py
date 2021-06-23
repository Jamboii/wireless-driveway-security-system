# Copy and execute this file from the /home/pi/ directory
from git import Repo
from git import RemoteProgress
import sys
import os

repo_path = "/home/pi/wireless-driveway-security"

# Check to make sure repository is on the system
def repo_get():
    # Assert that we have the repo
    assert os.path.isdir(repo_path)
    wds_repo = Repo(repo_path)
    print("repo")
    return wds_repo

# Make a pull of the repository code
def repo_pull(repo):
    origin = repo.remotes.origin
    print("origin")
    origin.fetch()
    print("fetched")
    origin.pull()
    print("pulled")


the_repo = repo_get()
repo_pull(the_repo)



