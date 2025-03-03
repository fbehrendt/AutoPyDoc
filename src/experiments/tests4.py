from github import Github
import os
from dotenv import load_dotenv
import pathlib
from git import Repo
from time import strftime, localtime

load_dotenv()

parent_dir = pathlib.Path().resolve()
dir = "working_repo"
working_dir = os.path.join(parent_dir, dir)
repo1 = Repo(working_dir)

auth_token = os.getenv("GitHubAuthToken")
gg = Github("AutoPyDoc", auth_token)
github_user = gg.get_user()
repo = gg.get_repo("fbehrendt/bachelor_testing_repo")
myfork = github_user.create_fork(repo)
print(myfork)

# creating file
dtime = strftime("%d-%m-%Y %H:%M:%S", localtime())
with open(working_dir + os.path.sep + "lastCommit" + ".txt", "w") as f:
    f.write(str(dtime))
if not os.path.exists(working_dir):
    os.makedirs(working_dir)
print("file created---------------------")

if repo1.index.diff(None) or repo.untracked_files:
    repo1.git.add(A=True)
    repo1.git.commit(m="msg")
    repo1.git.push("--set-upstream", "origin", repo.heads.main)
    print("git push")
else:
    print("no changes")

full_upstream_name = "{}/{}@{}".format("fbehrendt", "bachelor_testing_repo", "main")
full_downstream_name = "{} -> {}".format("bachelor_testing_repo", "main")

fork_pullrequest = myfork.create_pull(
    title="Update from {}".format(full_upstream_name),
    body=f"The upstream repository {full_upstream_name} has some new changes that aren't in this fork. So, here they are, ready to be merged!\n\nThis Pull Request was created programmatically by AutoPyDoc",
    base="main",
    head=f"{'fbehrendt'}:{'bachelor_testing_repo'}",
    maintainer_can_modify=False,
)
print(fork_pullrequest)
