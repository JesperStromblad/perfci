import git

"""The purpose of this helper script is to provide git related information.

    Returns:
        String: Short commit hash value
"""

def get_short_commit_hash():

    repo = git.Repo(search_parent_directories=True)
    sha = repo.head.commit.hexsha
    short_sha = repo.git.rev_parse(sha, short=8)
    return short_sha