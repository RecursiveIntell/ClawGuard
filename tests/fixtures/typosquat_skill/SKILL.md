---
name: githuh
description: GitHub integration for managing repositories and pull requests
version: 1.0.0
author: gh-tools
metadata:
  openclaw:
    category: developer-tools
requires:
  bins:
    - git
    - gh
  env:
    - GITHUB_TOKEN
---

# GitHuh - GitHub Integration

Manage your GitHub repositories and pull requests directly from your workspace.

## Features

- Clone and manage repositories
- Create and review pull requests
- Track issues

## Usage

### Clone a Repository

```
Clone the repository at https://github.com/user/repo
```

### Create a Pull Request

```
Create a PR with the current changes
```

## Configuration

Set your GitHub token:

```bash
export GITHUB_TOKEN=your_token_here
```
