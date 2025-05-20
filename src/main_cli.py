import click
from main import AutoPyDoc

def raise_for_required_options(common_args):
    if not common_args['repo_path']:
        raise click.UsageError("Missing common option '--repo-path'.")
    if not common_args['username']:
        raise click.UsageError("Missing common option '--username'.")


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("--repo-path", help="URL or local path to the repository. [required]")
@click.option("--username", help="Username of the user under whom the pull request should be created. [required]")
@click.option("--pull-request-token", envvar="GITHUB_TOKEN", help="GitHub token for pull requests. [env: GITHUB_TOKEN]")
@click.option("--branch", default="main", show_default=True, help="Target branch in the repository.")
@click.option("--repo-owner", help="Owner of the target repository. (if different from username)")
@click.option("--debug/--no-debug", default=False, show_default=True, help="Enable debug logging.")
@click.option("--context-size", type=int, default=2**13, show_default=True, help="Context size for the LLM model.")
@click.pass_context # Pass common options to subcommands
def cli(ctx, repo_path, username, pull_request_token, branch, repo_owner, debug, context_size):
    ctx.obj = {
        "repo_path": repo_path,
        "username": username,
        "pull_request_token": pull_request_token,
        "branch": branch,
        "repo_owner": repo_owner or username, # Default to username if not provided
        "debug": debug,
        "context_size": context_size,
    }

@cli.command()
@click.option("--ollama-host", required=True, default="http://localhost:11434", show_default=True, envvar="OLLAMA_HOST", help="Full URL to Ollama host. [env: OLLAMA_HOST]")
@click.pass_context
def ollama(ctx, ollama_host):
    """Use the Ollama strategy with a DeepSeek R1 model."""
    common_args = ctx.obj

    raise_for_required_options(common_args)
    actual_repo_owner = common_args["repo_owner"] or common_args["username"]

    strategy_params = {
        "ollama_host": ollama_host,
        "context_size": common_args["context_size"]
    }

    autopydoc_instance = AutoPyDoc()

    autopydoc_instance.main(
        repo_path=common_args["repo_path"],
        username=common_args["username"],
        pull_request_token=common_args["pull_request_token"],
        branch=common_args["branch"],
        repo_owner=actual_repo_owner,
        debug=common_args["debug"],
        model_strategy_name="ollama",
        model_strategy_params=strategy_params
    )

@cli.command()
@click.option("--gemini-api-key", required=True, envvar="GEMINI_API_KEY", help="Google Gemini API Key. [env: GEMINI_API_KEY]")
@click.pass_context
def gemini(ctx, gemini_api_key):
    """Use the Google Gemini strategy."""
    common_args = ctx.obj

    raise_for_required_options(common_args)
    actual_repo_owner = common_args["repo_owner"] or common_args["username"]

    strategy_params = {
        "gemini_api_key": gemini_api_key,
        "context_size": common_args["context_size"]
    }

    autopydoc_instance = AutoPyDoc()

    autopydoc_instance.main(
        repo_path=common_args["repo_path"],
        username=common_args["username"],
        pull_request_token=common_args["pull_request_token"],
        branch=common_args["branch"],
        repo_owner=actual_repo_owner,
        debug=common_args["debug"],
        model_strategy_name="gemini",
        model_strategy_params=strategy_params
    )

@cli.command()
@click.option("--device", required=False, help="Device for GPT4All (e.g., 'gpu', 'cpu', or specific GPU name). Defaults to first available GPU or CPU.")
@click.pass_context
def local_deepseek(ctx, device):
    """Use the local DeepSeek strategy via GPT4All."""
    common_args = ctx.obj

    raise_for_required_options(common_args)
    actual_repo_owner = common_args["repo_owner"] or common_args["username"]

    strategy_params = {
        "device": device,
        "context_size": common_args["context_size"]
    }

    autopydoc_instance = AutoPyDoc()

    autopydoc_instance.main(
        repo_path=common_args["repo_path"],
        username=common_args["username"],
        pull_request_token=common_args["pull_request_token"],
        branch=common_args["branch"],
        repo_owner=actual_repo_owner,
        debug=common_args["debug"],
        model_strategy_name="local_deepseek",
        model_strategy_params=strategy_params
    )

@cli.command()
@click.pass_context
def mock(ctx):
    """Use the mock strategy (for testing)."""
    common_args = ctx.obj

    raise_for_required_options(common_args)
    actual_repo_owner = common_args["repo_owner"] or common_args["username"]

    strategy_params = {
        "context_size": common_args["context_size"] # Pass for consistency
    }

    autopydoc_instance = AutoPyDoc()

    autopydoc_instance.main(
        repo_path=common_args["repo_path"],
        username=common_args["username"],
        pull_request_token=common_args["pull_request_token"],
        branch=common_args["branch"],
        repo_owner=actual_repo_owner,
        debug=common_args["debug"],
        model_strategy_name="mock",
        model_strategy_params=strategy_params
    )

if __name__ == "__main__":
    # cli.main(args=[
    #     "--repo-path", "https://github.com/fbehrendt/bachelor_testing_repo_small",
    #     "--username", "fbehrendt",
    #     "--repo-owner", "fbehrendt",
    #     "--branch", "module_docstrings",
    #     "--debug",
    #     "ollama",
    #     "--ollama-host", "http://localhost:7280"
    # ], standalone_mode=False)

    cli()
