import argparse

from main import AutoPyDoc

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AutoPyDoc for a repository")
    parser.add_argument(
        "repo_path",
        help="Repo Path",
    )
    parser.add_argument(
        "username",
        help="Username of the user under whom the pull request should be created",
    )
    parser.add_argument(
        "pull_request_token",
        help="Pull Request Token",
    )
    parser.add_argument(
        "branch",
        help="Branch",
    )
    parser.add_argument(
        "repo_owner",
        help="Owner of the target repository",
    )
    parser.add_argument(
        "ollama_host", help="Full URL to Ollama host (supports basic auth)", required=False
    )
    args = parser.parse_args()

    auto_py_doc = AutoPyDoc()
    auto_py_doc.main(
        repo_path=args.repo_path,
        username=args.username,
        pull_request_token=args.pull_request_token,
        branch=args.branch,
        ollama_host=args.ollama_host,
        repo_owner=args.repo_owner,
        debug=True,
    )
