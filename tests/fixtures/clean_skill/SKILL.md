---
name: github
description: GitHub integration for managing repositories, issues, and pull requests
version: 1.2.0
author: openclaw-community
license: MIT
metadata:
  openclaw:
    category: developer-tools
    verified: true
    downloads: 15420
requires:
  bins:
    - git
    - gh
  env:
    - GITHUB_TOKEN
  config:
    default_branch: main
---

# GitHub Integration

Manage your GitHub repositories, issues, and pull requests directly from your agent workspace.

## Features

- **Repository Management**: Clone, create, and manage repositories
- **Issue Tracking**: Create, list, update, and close issues
- **Pull Requests**: Open, review, and merge pull requests
- **Branch Operations**: Create, switch, and delete branches

## Usage

### List Issues

```
List all open issues in the current repository
```

### Create Pull Request

```
Create a PR from the current branch with a description of the changes
```

## Configuration

Set your GitHub token in the environment:

```bash
export GITHUB_TOKEN=your_token_here
```

The skill uses the `gh` CLI tool for authentication and API access.
All operations are scoped to repositories the authenticated user has access to.
