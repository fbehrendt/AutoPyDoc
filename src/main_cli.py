import argparse

from main import AutoPyDoc

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AutoPyDoc for a repository")
    parser.add_argument(
        "repo_path",
        help="Repo Path",
    )
    parser.add_argument(
        "pull_request_token",
        help="Pull Request Token",
    )
    parser.add_argument(
        "branch",
        help="Branch",
    )
    args = parser.parse_args()

    auto_py_doc = AutoPyDoc()
    auto_py_doc.main(
        repo_path=args.repo_path,
        pull_request_token=args.pull_request_token,
        branch=args.branch,
        debug=True,
    )
