const PLUGIN_CACHE_KEY = "pluginDataCache";
const PLUGIN_CACHE_TS_KEY = "pluginDataCache_ts";
const PLUGIN_API_URL = "https://rhcp.hazardcreative.com/v1/plugin/data.json";
const PROXY_URL = "https://api.allorigins.win/get?url=" + encodeURIComponent(PLUGIN_API_URL);

async function fetchPluginData(onUpdate = null, forceRefresh = false) {
    // 1️⃣ Load direct from cache
    const cachedRaw = localStorage.getItem(PLUGIN_CACHE_KEY);
    const cachedTs = localStorage.getItem(PLUGIN_CACHE_TS_KEY);
    let cachedParsed = [];

    if (!forceRefresh && window.pluginData) {
        return window.pluginData;
    }

    if (!forceRefresh && cachedRaw && cachedTs) {
        try {
            cachedParsed = Object.values(JSON.parse(cachedRaw));
            window.pluginData = cachedParsed;
        } catch {
            console.warn("⚠️ Cache corrupted");
        }
    }

    // 2️⃣ Start background fetch
    fetch(PROXY_URL)
        .then(res => res.ok ? res.json() : Promise.reject(res))
        .then(json => {
            const fetchedData = JSON.parse(json.contents);
            const fetchedParsed = Object.values(fetchedData);

            const cachedString = JSON.stringify(cachedParsed);
            const fetchedString = JSON.stringify(fetchedParsed);

            if (fetchedString !== cachedString || forceRefresh) {
                // 3️⃣ Update cache + notify
                localStorage.setItem(PLUGIN_CACHE_KEY, JSON.stringify(fetchedData));
                localStorage.setItem(PLUGIN_CACHE_TS_KEY, Date.now().toString());
                window.pluginData = fetchedParsed;
                if (typeof onUpdate === "function") onUpdate(fetchedParsed);
                // console.log("🔄 Plugin data updated from background fetch");
            } else {
                // console.log("✅ Plugin data is still up to date");
            }
        })
        .catch(err => console.error("❌ Background fetch failed:", err));

    // 4️⃣ Return cached data immediately
    return cachedParsed;
}
