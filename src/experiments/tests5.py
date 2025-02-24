from github import Github
from github import InputGitAuthor
import os
from dotenv import load_dotenv
from git import Repo
import pathlib
from time import strftime, localtime
from os import path

load_dotenv()

auth_token = os.getenv('GitHubAuthToken')

# Authentication is defined via github.Auth
from github import Auth

# using an access token
auth = Auth.Token(auth_token)

# First create a Github instance:



def commit_files_and_create_branch(repo, working_dir, branch):
    if repo != None:
        new_branch = branch + "_AutoPyDoc"
        current = repo.create_head(new_branch)
        current.checkout()
        main = repo.heads.main
        repo.git.pull('origin', main)
        #creating file
        dtime = strftime('%d-%m-%Y %H:%M:%S', localtime())
        with open(working_dir + path.sep + 'lastCommit' + '.txt', 'w') as f:
            f.write(str(dtime))
        if not path.exists(working_dir):
            os.makedirs(working_dir)
        print('file created---------------------')

        if repo.index.diff(None) or repo.untracked_files:

            repo.git.add(A=True)
            repo.git.commit(m='msg')
            repo.git.push('--set-upstream', 'origin', current)
            print('git push')
        else:
            print('no changes')
        return new_branch
    raise Exception

def create_pull_request(repo_name, title, description, head_branch, base_branch, git_token):
    # Public Web Github
    github_object = Github("AutoPyDoc", auth_token)
    repo = github_object.get_repo(repo_name)

    pull_request = repo.create_pull(
        title=title,
        body=description,
        head=head_branch,
        base=base_branch
    )
    # To close connections after use
    github_object.close()
    return pull_request


if __name__ == "__main__":
    load_dotenv()
    auth_token = os.getenv('GitHubAuthToken')
    
    parent_dir = pathlib.Path().resolve()
    dir = "working_repo"
    working_dir = os.path.join(parent_dir, dir)
    repo = Repo(working_dir)
    branch = "main"
    new_branch = commit_files_and_create_branch(repo, working_dir, branch)
    pull_request = create_pull_request(repo_name="fbehrendt/bachelor_testing_repo", title="test", description="Testing pull requests", head_branch=new_branch, base_branch=branch, git_token=auth_token)
    print(pull_request)