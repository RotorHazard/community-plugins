---
id: include
title: Include repository
description: How to include your plugin repository in the plugin database
---

This guide will help you add your plugin repository to the community plugins database.

## Prepare your repository

Before submitting your plugin repository, make sure it meets all the [requirements](index.md#requirements) listed in the Getting Started guide.

## Add your plugin

To add your plugin to the community plugins database, follow the steps below.

!!! warning "Create a separate PR for each plugin"
    Want to add multiple plugins? Submit a separate pull request for each one. Keeping PRs small aligns with GitHub's best practices and makes the review process much easier.

1. Fork the [community plugins](https://github.com/RotorHazard/community-plugins) repository and create a feature branch for your changes.
2. Add your plugin to the [`plugins.json`][plugins] file, with the format (`"owner/repo"`).
3. Add your plugin to the [`categories.json`][categories] file, assigning it to a valid category.
4. Commit your changes.
5. Open a pull request and follow the instructions in the PR template.

???+ tip "Sort a JSON file"
    There is a special script in the repository that can sort the json files alphabetically for you in case-insensitive order.

    ```bash
    python scripts/sort_json.py plugins.json
    ```

??? tip "use pre-commit to ensure quality commits"
    [Pre-commit](https://pre-commit.com/) ensures that quality commits are pushed and you also know immediately if problems arise that can be solved in advance. To install pre-commit, run the following command inside your virtual environment (.venv):

    ```bash
    pre-commit install
    ```

## CI Checks

After submitting your pull request, a series of CI checks (pre-flights) will be run to ensure that the repository meets the required standards to be included in the community plugins database. All checks must pass for the repository to be included, unless otherwise agreed.

### Check Category

Check whether the plugin repository is assigned to a valid category. The list of categories can be found in the [`categories.json`][categories] file.

### Check Releases

We expect at least 1 release to be published in the added repository. More about this can also be found on the [Getting started](index.md#github-releases) page.

### Check Removed

Check whether the plugin repository is on the list of previously removed plugins. If it is, the plugin will not be accepted/included in the community plugins database. The list of removed plugins can be found in the [`removed.json`][removed] file.

### RHFest validation

Check that the `manifest.json` file and repository structure are valid. More details can be found on the dedicated [RHFest](../rhfest/index.md) page.

### Lint [jq]

This check makes sure that all JSON files are valid.

### Lint [jsonschema]

This check makes sure that the files `plugins.json`, `removed.json` and `categories.json` are valid according to a JSON schema.

### Lint [sorted]

This makes sure that the files `removed.json` and `plugins.json` are alphabetically sorted.

## After submitting

After you submit your pull request, a maintainer will review it to ensure all requirements are met. If all checks pass, your PR will be approved and merged.

Once merged, the metadata update will be processed automatically during the next scheduled cycle, which runs every 2 hours. After that, users will be able to find and install your plugin directly through the RotorHazard UI.

<!-- LINKS -->
[categories]: https://github.com/RotorHazard/community-plugins/blob/main/categories.json
[removed]: https://github.com/RotorHazard/community-plugins/blob/main/removed.json
[plugins]: https://github.com/RotorHazard/community-plugins/blob/main/plugins.json
