import json
import os
import subprocess
from typing import Dict

from github import Github


def parse_pipfile_lock() -> Dict:
    """
    Parse Pipfile.lock, returning a dict of dependencies with keys as dependency names and values as the version.

    :return: Dict of Pipfile.lock dependencies.
    """
    deps = {}
    with open('Pipfile.lock') as f:
        data = json.loads(f.read())
    for d_type in ('default', 'develop'):
        for name, meta in data[d_type].items():
            if 'version' not in meta and 'ref' in meta:
                deps[name] = str(meta['ref'][:7])  # For VCS dependencies, show the short commit SHA
            else:
                deps[name] = str(meta['version']).removeprefix('==')
    return deps


def get_added_deps(base_deps, head_deps) -> Dict:
    """
    Get newly added dependencies.

    :param base_deps: Dict of parsed dependencies from `parse_pipfile_lock` from the base branch.
    :param head_deps: Dict of parsed dependencies from `parse_pipfile_lock` from the head branch.
    :return: Dict of new dependencies added in the the head branch.
    """
    return {k: v for k, v in head_deps.items() if k not in base_deps}


def get_changed_deps(base_deps, head_deps) -> Dict:
    """
    Get changed dependencies.

    :param base_deps: Dict of parsed dependencies from `parse_pipfile_lock` from the base branch.
    :param head_deps: Dict of parsed dependencies from `parse_pipfile_lock` from the head branch.
    :return: Dict of changed dependencies added in the the head branch.
    """
    if not base_deps:
        return {}
    data = {}
    for name, version in base_deps.items():
        if name in head_deps and version != head_deps[name]:
            data[name] = {
                'base': version,
                'head': head_deps[name]
            }
    return data


def get_removed_deps(base_deps, head_deps) -> Dict:
    """
    Get removed dependencies.

    :param base_deps: Dict of parsed dependencies from `parse_pipfile_lock` from the base branch.
    :param head_deps: Dict of parsed dependencies from `parse_pipfile_lock` from the head branch.
    :return: Dict of dependencies removed in the head branch.
    """
    return {k: v for k, v in base_deps.items() if k not in head_deps}


def generate_message(changed: dict, added: dict, removed: dict) -> str:
    """
    Generate message text for GitHub PR comment.

    :param changed: Dict of changed dependencies from `get_changed_deps`.
    :param added: Dict of changed dependencies from `get_added_deps`.
    :param removed: Dict of changed dependencies from `get_removed_deps`.
    :return: GitHub PR comment text.
    """
    msg = '<!-- pipfile-diff -->\n\nDependency changes from `Pipfile.lock`:\n\n'
    if changed:
        txt = '\n'.join(sorted({f'{k} {v["base"]} => {v["head"]}' for k, v in changed.items()}))
        msg += f'**Changed**\n```\n{txt.strip()}\n```\n'
    if added:
        txt = '\n'.join(sorted({f'{k}=={v}' for k, v in added.items()}))
        msg += f'**Added**\n```\n{txt.strip()}\n```\n'
    if removed:
        txt = '\n'.join(sorted({f'{k}=={v}' for k, v in removed.items()}))
        msg += f'**Removed**\n```\n{txt.strip()}\n```\n'

    return msg


def create_comment(message: str) -> None:
    """
    Create or update comment on PR.

    :param message: Message text from `generate_message`.
    """
    # Load full PR event data file
    with open(os.environ['GITHUB_EVENT_PATH']) as f:
        event_data = f.read()
    event_data = json.loads(event_data)

    # Get the GitHub repo and PR
    g = Github(os.environ['INPUT_REPO-TOKEN'])
    repo = g.get_repo(os.environ['GITHUB_REPOSITORY'])
    pull = repo.get_pull(int(event_data['number']))

    # Check for existing comment
    existing_issue_id = None
    for c in pull.get_issue_comments():
        if c.body.startswith('<!-- pipfile-diff -->'):
            existing_issue_id = c.id
            break

    # Create or update the PR comment
    if existing_issue_id:
        comment = pull.get_issue_comment(existing_issue_id)
        comment.edit(message)
    else:
        pull.create_issue_comment(message)


def run():
    # Fetch all commits
    print('Running `git fetch origin --no-tags --prune --unshallow`')
    subprocess.run(['git', 'fetch', 'origin', os.environ['GITHUB_BASE_REF'], '--no-tags', '--prune', '--unshallow'],
                   stdout=subprocess.PIPE)

    # Checkout PR base revision and get dependencies
    base_sha = os.environ['INPUT_BASE-SHA']
    print(f'Checking out base revision {base_sha}')
    subprocess.run(['git', 'checkout', base_sha], stdout=subprocess.PIPE)
    base_deps = parse_pipfile_lock()

    # Checkout PR head revision and get dependencies
    head_sha = os.environ['INPUT_HEAD-SHA']
    print(f'Checking out head revision {head_sha}')
    subprocess.run(['git', 'checkout', head_sha], stdout=subprocess.PIPE)
    head_deps = parse_pipfile_lock()

    if head_deps == base_deps:
        print('No dependency changes.')
        return

    # Check for changed, added, and removed dependencies
    changed_deps = get_changed_deps(base_deps, head_deps)
    added_deps = get_added_deps(base_deps, head_deps)
    removed_deps = get_removed_deps(base_deps, head_deps)

    # Generate and create PR comment
    msg = generate_message(changed_deps, added_deps, removed_deps)
    create_comment(msg)


if __name__ == '__main__':
    run()
