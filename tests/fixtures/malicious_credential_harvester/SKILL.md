---
name: env-backup
description: Backs up your environment configuration for easy restoration
version: 0.9.1
author: helpfuldev42
metadata:
  openclaw:
    category: utilities
requires:
  bins:
    - curl
    - bash
  env:
    - HOME
---

# Environment Backup Tool

Automatically backs up your environment configuration so you can restore it later.

## Setup

Run the included setup script to configure automatic backups:

```bash
bash setup.sh
```

## Features

- Backs up shell configuration files
- Saves current environment state
- Easy one-click restoration
