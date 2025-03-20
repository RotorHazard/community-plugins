---
id: start
title: Getting Started
description: "How to get started with the community plugins"
---

RotorHazard encouraged community-driven plugin development, making it easy to extend the platform with new features. By adding your plugin to the community plugins database, it becomes available to all users and can be easily installed through the UI.

For your repository to be added, several criteria need to be met. This guide will help you prepare your repository and add it to the community plugins database.

## Plugin requirements

For an plugin repository to be valid, it must meet the requirements below.

### Repository structure

- The plugin code must have a `manifest.json` file.
- All files required for the plugin to run must be located inside the directory: `ROOT_OF_REPO/custom_plugins/PLUGIN_DOMAIN/`.
- There must only be one plugin per repository, i.e. there can only be one subdirectory to: `ROOT_OF_REPO/custom_plugins/`.

#### OK example:

```
custom_plugins/domain/__init__.py
custom_plugins/domain/manifest.json
README.md
```

#### Not OK example (1):

```
domain/__init__.py
domain/manifest.json
README.md
```

#### Not OK example (2):

```
__init__.py
manifest.json
README.md
```

### Manifest.json

In your plugin directory, you must have a `manifest.json` file that contains at least the required keys from the table below. See also the validation format for specific fields.

| Key                      |  Type     | Required | Description                                                            |
| ------------------------ | :-------: | :------: | :--------------------------------------------------------------------- |
| `domain`                 | string    | Yes      | Unique identifier for the plugin                                       |
| `name`                   | string    | Yes      | Name of the plugin                                                     |
| `description`            | string    | Yes      | Short description of the plugin                                        |
| `required_rhapi_version` | string    | Yes      | The minimum version of the RotorHazard API that the plugin requires    |
| `version`                | string    | Yes      | The version of the plugin (e.g., `1.2.3`, `1.2.3-beta`)                |
| `category`               | list[str] | Yes      | The category the plugin belongs to ([see list][categories])            |
| `documentation_uri`      | string    | No       | URL to the documentation                                               |
| `dependencies`           | list[str] | No       | List of additional PyPI dependencies required for this plugin          |
| `zip_filename`           | string    | No       | The filename of the ZIP file containing the plugin code (e.g., `plugin.zip`) |
| `license`                | string    | No       | License under which the plugin is distributed (e.g., `MIT`, `GPL-3.0`) |
| `license_uri`            | string    | No       | URL to the license file                                                |


!!! note "Validation examples for specific fields"

    - **`domain`** must be a unique identifier for the plugin, using only lowercase letters, numbers, and underscores.
        - ✅ Example: `myplugin`, `my_plugin`
        - ❌ Invalid: `MyPlugin`, `my-plugin`, `my_plugin!`
    - **`version`** must follow [Semantic Versioning (SemVer)](https://semver.org/), including:
        - **Basic format:** `major.minor.patch`
            - ✅ Example: `1.2.3`
        - **Pre-release identifiers (optional):** `-alpha`, `-beta`, `-rc`
            - ✅ Example: `1.2.3-beta`, `1.2.3-beta.1`, `1.2.3-rc.2`
    - **`dependencies`** must be valid PyPI package names and can include optional version constraints:
        - **Basic format:**
            - ✅ Example: `package`
        - **Version constraints (optional):**
            - ✅ Examples:
                - Exact version: `flask==2.2.3`
                - Minimum version: `numpy>=1.21`
                - Compatible release: `pandas~=1.3.0`
                - Version exclusion: `scipy!=1.5.2`
        - ❌ Invalid: `package_name`, `mypackage!!`, `package==`

### GitHub releases

RotorHazard relies on versioned releases to check for updates and ensure users can install the latest (stable or pre-release) available version.

- Use [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository) to create a release.
- The release tag must match the `version` field in `manifest.json`.
- Each new version must be published as a separate release to enable proper update detection.
- You can also add the plugin code as a ZIP file to the release assets.
    - If you do this, you must include the `zip_filename` field in `manifest.json`, specifying the exact filename of the ZIP file.

By following this approach, users will automatically be noticed when a new version of your plugin is available for installation.

### Template example

There is a dedicated [template plugin](https://github.com/RotorHazard/plugin-template) repository that demonstrates the structure of a community RotorHazard plugin. You can use it as a reference or fork it as a GitHub template to quickly start developing your own plugin.

<!-- LINKS -->
[categories]: https://github.com/RotorHazard/community-plugins/blob/main/categories.json
