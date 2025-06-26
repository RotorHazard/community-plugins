const PLUGIN_CACHE_KEY = "pluginDataCache";
const PLUGIN_CACHE_TS_KEY = "pluginDataCache_ts";
const PLUGIN_API_URL = "https://rhcp.hazardcreative.com/v1/plugin/data.json";
const CATEGORIES_API_URL = "https://rhcp.hazardcreative.com/v1/plugin/categories.json";

async function fetchPluginData(onUpdate = null, forceRefresh = false) {
    // Check local cache
    const cachedRaw = localStorage.getItem(PLUGIN_CACHE_KEY);
    const cachedTs = localStorage.getItem(PLUGIN_CACHE_TS_KEY);
    if (!forceRefresh && window.pluginData) {
        return window.pluginData;
    }
    if (!forceRefresh && cachedRaw && cachedTs) {
        try {
            const cachedParsed = JSON.parse(cachedRaw);
            window.pluginData = cachedParsed;
            return cachedParsed;
        } catch {
            console.warn("⚠️ Cache corrupted");
        }
    }

    // Fetch both in parallel
    try {
        const [pluginJson, catJson] = await Promise.all([
            fetch(PLUGIN_API_URL).then(res => res.ok ? res.json() : Promise.reject(res)),
            fetch(CATEGORIES_API_URL).then(res => res.ok ? res.json() : Promise.reject(res))
        ]);

        const pluginData = pluginJson;
        const categoryData = catJson;

        // repo → [categories]
        const repoToCategories = {};
        Object.entries(categoryData).forEach(([cat, repos]) => {
            repos.forEach(repo => {
                if (!repoToCategories[repo]) repoToCategories[repo] = [];
                repoToCategories[repo].push(cat);
            });
        });

        // Combine: plugin.categories (always array)
        const plugins = Object.values(pluginData).map(plugin => ({
            ...plugin,
            categories: repoToCategories[plugin.repository] || [],
        }));

        // Console log for debug
        // console.log("🔗 Combined plugin data with categories:", plugins);

        // Update cache + notify
        localStorage.setItem(PLUGIN_CACHE_KEY, JSON.stringify(plugins));
        localStorage.setItem(PLUGIN_CACHE_TS_KEY, Date.now().toString());
        window.pluginData = plugins;
        if (typeof onUpdate === "function") onUpdate(plugins);

        return plugins;
    } catch (err) {
        console.error("❌ Background fetch failed:", err);
        return [];
    }
}
