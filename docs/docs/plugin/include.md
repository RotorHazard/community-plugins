---
id: include
title: Include repository
description: How to include your plugin repository in the plugin database
---

This guide will help you add your plugin repository to the community plugins database.

## Prepare your repository

Before submitting your plugin repository, make sure it meets the requirements below.

- Make the repository public.
- Add [RHFest](https://github.com/RotorHazard/rhfest-action) validation action to your repository and make sure it passes.
- Publish at least 1 release, this is required for the CI checks.

## Add your plugin

To add your plugin to the community plugins database, follow the steps below.

1. Fork the [community plugins](https://github.com/RotorHazard/community-plugins) repository.
2. Create a feature branch and add your plugin (format: `"owner/repo"`) to the [`plugins.json`](https://github.com/RotorHazard/community-plugins/blob/main/plugins.json).
3. Commit your changes.
4. Open a pull request and follow the instructions in the PR template.

!!! note
    Want to add multiple plugins? Submit a separate pull request for each one. Keeping PRs small aligns with GitHub's best practices and makes the review process much easier.

## CI Checks

After submitting your pull request, a series of CI checks will be run to ensure that the repository meets the required standards to be included in the community plugins database. All checks must pass for the repository to be included, unless otherwise agreed.

### Check Releases

We expect at least 1 release to be published in the added repository. More about this can also be found on the [Getting started](index.md#github-releases) page.

### Check Removed

Check whether the plugin repository is on the list of previously removed plugins.

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
