# AutoPyDoc

Tool to automatically generate and update docstrings for Python code for use in GitHub Actions.

## Add autopydoc.yml to your repository

Usage:
copy autopydoc.yml to .github/workflows in your repository
edit autopydoc.yml and replace <target repo name> with your repositories name, <username> with the user the repository is from and <your username> with the user that should create the new branch for the pull request.

## Add an authentication token

Go to https://github.com/settings/profile
-> Developer settings
-> Personal access tokens
-> Fine-grained tokens

Token name: Access Token AutoPyDoc
Expiration: your choice
Repository access->only selected repositories:
- your repository
Permissions:
Contents: read and write
pull requests: read and write
secrets: read only

copy this token

Go to `https://github.com/<user>/<repo>/settings/secrets/actions`
-> new repository secret
Name: FULL_ACCESS_TOKEN
Secret: <paste the token>

-> new repository secret
Name: PULL_REQUEST_TOKEN
Secret: <paste the same token>

## Development Setup

```
# Install dependencies
uv sync

# Run the CLI
uv run src/main_cli.py
```
