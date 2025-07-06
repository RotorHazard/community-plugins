const PLUGIN_API_URL = "https://rhcp.hazardcreative.com/v1/plugin/data.json";
const CATEGORIES_API_URL = "https://rhcp.hazardcreative.com/v1/plugin/categories.json";

/**
 * Fetches and combines plugin data with category mappings.
 *
 * @param {Function|null} onUpdate - Optional callback to invoke with fresh plugin data.
 * @param {boolean} forceRefresh - Force re-fetching even if window.pluginData is already loaded.
 * @returns {Promise<Array>} - Combined plugin data array.
 */
async function fetchPluginData(onUpdate = null, forceRefresh = false) {
    if (!forceRefresh && window.pluginData) {
        return window.pluginData;
    }

    try {
        const [pluginJson, categoryJson] = await Promise.all([
            fetch(PLUGIN_API_URL).then(res => res.ok ? res.json() : Promise.reject(new Error(`Plugin fetch failed: ${res.status}`))),
            fetch(CATEGORIES_API_URL).then(res => res.ok ? res.json() : Promise.reject(new Error(`Category fetch failed: ${res.status}`))),
        ]);

        // Create a mapping of repository → [categories]
        const repoToCategories = {};
        for (const [category, repos] of Object.entries(categoryJson)) {
            for (const repo of repos) {
                if (!repoToCategories[repo]) {
                    repoToCategories[repo] = [];
                }
                repoToCategories[repo].push(category);
            }
        }

        // Merge plugin data with their category assignments
        const plugins = Object.values(pluginJson).map(plugin => ({
            ...plugin,
            categories: repoToCategories[plugin.repository] || [],
        }));

        window.pluginData = plugins; // cache in-memory
        if (typeof onUpdate === "function") onUpdate(plugins);

        return plugins;
    } catch (error) {
        console.error("❌ Failed to load plugin data:", error);
        window.pluginData = [];
        if (typeof onUpdate === "function") onUpdate([]);
        return [];
    }
}
