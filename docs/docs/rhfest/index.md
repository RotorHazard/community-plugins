---
id: rhfest
title: RHFest Action
description: A GitHub action that validates a RotorHazard plugin
---

# RHFest Action

RHFest is a GitHub action that validates a RotorHazard plugin for several things, such as the folder structure in the repository and the keys defined in the `manifest.json`.

## Usage

Plugin authors can add the following GitHub workflow to their plugin repository:

```yaml
name: RHFest

on:
  push:
    branches:
      - main
  pull_request:
  schedule:
    - cron: "0 0 * * *" # Every day at midnight

jobs:
  validation:
    name: Validation
    runs-on: ubuntu-latest
    steps:
      - name: ⤵️ Check out code from GitHub
        uses: actions/checkout@v4.2.2

      - name: 🚀 Run RHFest validation
        uses: docker://ghcr.io/rotorhazard/rhfest-action:latest
```

This workflow will run the RHFest validation every day at midnight and on every push to the `main` branch.

## Related links

- [RHFest GitHub repository](https://github.com/RotorHazard/rhfest-action)
- [RHFest Docker image](https://github.com/RotorHazard/rhfest-action/pkgs/container/rhfest-action)
