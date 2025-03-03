from github import Github
from github import InputGitAuthor
import os
from dotenv import load_dotenv

load_dotenv()

auth_token = os.getenv("GitHubAuthToken")

# Authentication is defined via github.Auth
from github import Auth

# using an access token
auth = Auth.Token(auth_token)

# First create a Github instance:

# Public Web Github
github_object = Github(auth=auth)

repo = github_object.get_repo("fbehrendt/bachelor_testing_repo")

file = repo.get_contents("src/main.py")
new_file_content = "updated file content"
file_message = "Update src/main.py"
repo.update_file("src/main.py", file_message, new_file_content, file.sha)

# Commit the changes
author = InputGitAuthor("AutoPyDoc", "alltheunnecessaryjunk@gmail.com")
commit_message = "Updated multiple files"
new_tree = repo.create_git_tree(tree_new)
commit = repo.create_git_commit(commit_message, new_tree.sha, [branch.commit.sha])
repo.get_git_ref("heads/master").commit(
    "New commit",
    repo.get_contents("src/main.py").sha,
    author=author,
    committer=author,
    tree=repo.get_git_tree("master").sha,
)

body = """
SUMMARY
Change HTTP library used to send requests

TESTS
  - [x] Send 'GET' request
  - [x] Send 'POST' request with/without body
"""

pull_request = repo.create_pull(
    title="Pull Request Title", body="Pull Request Body", head="main", base="master"
)
# To close connections after use
github_object.close()
