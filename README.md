# RotorHazard Community Plugins

This project contains the database generation code for the list of community plugins for RotorHazard.

## Add a new plugin

1. Fork this repository.
2. Create a new branch from the **main** branch.
3. Add your plugin to the `plugins.json` file.
4. Create a pull request.

### Before submitting

If you apply the [plugin template][plugin-template] to an existing RotorHazard plugin that uses GitHub releases, please note that the community store / plugin install manager is only compatible with published releases that also pass the [RHFest][rhfest-action] checks.

## 🌟 Credits

This project is inspired by the way how [HACS](https://hacs.xyz/) handles the metadata database of custom integrations for Home Assistant.

## License

Distributed under the **MIT** License. See [`LICENSE`](LICENSE) for more information.

<!-- Links -->
[plugin-template]: https://github.com/rotorhazard/plugin-template
[rhfest-action]: https://github.com/rotorhazard/rhfest-action
