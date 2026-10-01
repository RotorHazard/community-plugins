---
id: rhfest
title: RHFest Action
description: Automated validation for RotorHazard plugins via GitHub Actions
hide:
  - navigation
---

# RHFest Action

**RHFest** validates RotorHazard plugin repositories against the official structure, manifest, and Python entry-point requirements. It checks the repository layout, validates every supported `manifest.json` field, confirms that the plugin folder matches the manifest `domain`, parses the plugin source, validates `initialize(rhapi)`, and detects access to private RHAPI internals.

This helps plugin authors maintain consistent quality and catch problems before release. It is also a mandatory part if you want to add a plugin to the database.

## How it works

Once configured, RHFest runs automatically whenever code is pushed or a pull request is opened. It reports stable rule codes, source locations, and help text directly in the GitHub Actions logs. Errors fail the workflow; warnings remain visible without failing validation.

## Benefits

Using RHFest ensures your plugin remains compliant with RotorHazard requirements:

- Detects issues automatically during development
- Validates pull requests and main branch updates
- Can run on a daily schedule to verify ongoing compliance
- Can run locally through pre-commit or Docker
- Reports stable rule codes that can be selected or suppressed explicitly
- Reduces manual review effort and improves consistency

## Installation

!!! tip "Start from the official template"
    The RHFest workflow is already included by default in the [plugin template repository](https://github.com/RotorHazard/plugin-template). If you are starting from that template, no further setup is required.

For existing repositories, create a new file at `.github/workflows/rhfest.yaml` and add the following content:

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
    permissions:
      contents: read
    steps:
      - name: ⤵️ Check out code from GitHub
        uses: actions/checkout@v7.0.1

      - name: 🚀 Run RHFest validation
        uses: RotorHazard/rhfest-action@v3.2.3
```

This configuration runs RHFest automatically on pushes to `main`, on pull requests, and once per day. The complete release tag keeps validation reproducible. Update it deliberately when a newer RHFest release is available, for example through Renovate.

### Selecting or ignoring rules

RHFest groups its stable rule codes into repository structure (`STR`), manifest (`MAN`), and RotorHazard Python source (`RH`) families. Use Action inputs to adopt a family incrementally or suppress a deliberate exception:

```yaml
      - name: 🚀 Run selected RHFest validation
        uses: RotorHazard/rhfest-action@v3.2.3
        with:
          select: "STR,MAN,RH002"
          ignore: "MAN002"
```

`ignore` is applied after `select` and therefore takes precedence. Unknown or partial rule codes are configuration errors. See the [RHFest rule catalog](https://github.com/RotorHazard/rhfest-action/blob/main/docs/rules.md) for the complete list and remediation guidance.

## Pre-commit

RHFest is also available as an official Docker-based pre-commit hook. The example pins a complete release so every contributor runs the same RHFest version:

```yaml
repos:
  - repo: https://github.com/RotorHazard/rhfest-action
    rev: v3.2.3
    hooks:
      - id: rhfest
        name: 🎉 Check RHFest
        stages: [pre-commit, pre-push, manual]
```

Docker must be available when the hook runs. Pre-commit builds RHFest from the selected release and caches the resulting image for later checks. Run `pre-commit autoupdate` periodically to update the configuration to the latest published RHFest tag while keeping the selected version explicit and reproducible.

## Run locally with Docker

You can run the same validation manually from the root of a plugin repository:

```bash
docker run --rm -v "$(pwd):/repo" ghcr.io/rotorhazard/rhfest-action:v3.2.3
```

Selection flags are also available when running the container directly:

```bash
docker run --rm -v "$(pwd):/repo" \
  ghcr.io/rotorhazard/rhfest-action:v3.2.3 \
  --select STR,MAN,RH002 --ignore MAN002
```

## Results and reporting

When the workflow completes, you can view the results in the Actions tab of your repository. A green checkmark means validation succeeded. If validation fails, the annotations and logs identify the rule code, affected file and source location, and provide guidance when an automatic fix is not possible.

You can add a validation status badge to your README:

```markdown
![RHFest](https://github.com/your-username/your-plugin/actions/workflows/rhfest.yaml/badge.svg)
```

This badge updates automatically to reflect the latest validation result.

## Learn more

- [RHFest GitHub repository](https://github.com/RotorHazard/rhfest-action)
- [RHFest Docker image](https://github.com/RotorHazard/rhfest-action/pkgs/container/rhfest-action)
- [Plugin tutorial](../plugin/tutorial.md) - Learn how to create a plugin
- [Manifest reference](../plugin/index.md#manifestjson) - Details about the manifest.json file
