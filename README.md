# Pipfile diff

Pull request comments for dependency changes in Pipfile.lock.

![Screenshot](img/screenshot.png)

## Features

- Tracks changed, removed, and new dependencies in `Pipfile.lock`
- Support for VCS dependencies in `Pipfile.lock`

## Limitations

- Currently, only checks for changes in `Pipfile.lock`, which can result in overwhelming comments including all
  sub-dependencies

## TODO

- [ ] Add input for choice of `Pipfile`/`Pipfile.lock` checking
- [ ] Write tests 💪

## Inputs

| Name         | Default                              | Description                                                                 |
|--------------|--------------------------------------|-----------------------------------------------------------------------------|
| `base-sha`   | `github.event.pull_request.base.sha` | The base commit SHA to compare dependencies against.                        |
| `head-sha`   | `github.event.pull_request.head.sha` | The head commit SHA to compare dependencies against.                        |
| `repo-token` | `github.token`                       | The token for this action, allowing the action to comment on pull requests. |