import git
import datetime
import os
from time import *
from os import path
from git import Repo
import pathlib
from dotenv import load_dotenv

def commit_files_and_create_branch(repo, working_dir):
    if repo != None:
        new_branch = 'your_new_branch_3'
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

import json
import requests

def create_pull_request(project_name, repo_name, title, description, head_branch, base_branch, git_token):
    """Creates the pull request for the head_branch against the base_branch"""
    git_pulls_api = "https://github.com/api/v3/repos/{0}/{1}/pulls".format(
        project_name,
        repo_name)
    headers = {
        "Authorization": "token {0}".format(git_token),
        "Content-Type": "application/json"}

    payload = {
        "title": title,
        "body": description,
        "head": head_branch,
        "base": base_branch,
    }

    r = requests.post(
        git_pulls_api,
        headers=headers,
        data=json.dumps(payload))

    if not r.ok:
        print("Request Failed: {0}".format(r.text))



if __name__ == "__main__":
    load_dotenv()
    auth_token = os.getenv('GitHubAuthToken')
    parent_dir = pathlib.Path().resolve()
    dir = "working_repo"
    working_dir = os.path.join(parent_dir, dir)
    repo = Repo(working_dir)
    main = repo.heads.main.name
    new_branch = commit_files_and_create_branch(repo, working_dir)
    create_pull_request(
        "bachelor_testing_project", # project_name
        "bachelor_testing_repo", # repo_name
        "Docstrings generated by AutoPyDOc", # title
        "This pull request contains automatically created docstrings for recent code changes", # description
        new_branch, # head_branch
        main, # base_branch
        auth_token, # git_token
    )