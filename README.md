# gway-request

Gway-native request helpers for creating issues against installed projects.

## Install

```bash
gway install request
```

## Create an issue

`issue` is the project's default command, so it can be omitted:

```bash
gway request lcd "LCD write fails after stopping legacy service"
```

The explicit form remains valid:

```bash
gway request issue lcd "LCD write fails after stopping legacy service"
```

For multi-line text, the first non-empty line becomes the GitHub issue title and the remaining lines become the body.

`gway-request` resolves the installed project with `gway path <project>`, reads that checkout's Git `origin`, and creates the issue in the corresponding GitHub repository.

Authentication uses the GitHub CLI when `gh` is installed. If it is not available, set `GH_TOKEN` or `GITHUB_TOKEN` and the package will use the GitHub REST API directly.
