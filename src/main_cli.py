import argparse

from main import AutoPyDoc

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AutoPyDoc for a repository")
    parser.add_argument(
        "-r",
        "--repo",
        help="Repo Path",
    )
    parser.add_argument(
        "-t",
        "--token",
        help="Pull Request Token",
    )
    args = parser.parse_args()

    auto_py_doc = AutoPyDoc()
    auto_py_doc.main(repo_path=args.repo, pull_request_token=args.token, debug=True)
