import sys
from main import AutoPyDoc

if __name__ == "__main__":
    auto_py_doc = AutoPyDoc()
    auto_py_doc.main(repo_path=sys.argv[1], pull_request_token=sys.argv[2], debug=True)
