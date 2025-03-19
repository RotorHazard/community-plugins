async function fetchPluginData() {
    if (window.pluginData) {
        // console.log("✅ Plugin data from cache");
        return window.pluginData;
    }

    // console.log("🔄 Fetching plugin data...");
    const url = "https://api.allorigins.win/get?url=" + encodeURIComponent("https://rhcp.hazardcreative.com/v1/plugin/data.json");

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Response status: ${response.status}`);

        const json = await response.json();
        window.pluginData = Object.values(JSON.parse(json.contents)); // Cache data
        return window.pluginData;

    } catch (error) {
        console.error("❌ Error loading plugin data:", error);
        return [];
    }
}
