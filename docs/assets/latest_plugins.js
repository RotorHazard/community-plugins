// Fetches the latest plugin metadata from the RHCP API and displays it on the page
async function loadPlugins() {
    // console.log("🔄 Loading plugins...");
    const url = "https://api.allorigins.win/get?url=" + encodeURIComponent("https://rhcp.hazardcreative.com/v1/plugin/data.json");

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }

        // Parse JSON from AllOrigins
        const json = await response.json();
        const data = Object.values(JSON.parse(json.contents)); // Convert object to array

        // Sort by last_updated and take the latest 6
        const latestPlugins = data
            .sort((a, b) => new Date(b.last_updated) - new Date(a.last_updated))
            .slice(0, 6);

        const container = document.getElementById("plugin-container");
        container.innerHTML = ""; // Clear old cards

        latestPlugins.forEach(plugin => {
            const manifest = plugin.manifest;
            const card = document.createElement("div");
            card.classList.add("plugin-card");

            // Build card content
            card.innerHTML = `
                <span class="version-badge">${manifest.version}</span>
                <h2>${manifest.name}</h2>
                <p class="plugin-description">${manifest.description}</p>
                <p><strong>Auteur:</strong> <a href="${manifest.author_uri}" target="_blank">${manifest.author}</a></p>
                <p><strong>Categorie:</strong> ${manifest.category.join(', ')}</p>
                ${plugin.repository ? `<p><strong>Repo:</strong> <a href="https://github.com/${plugin.repository}" target="_blank">${plugin.repository}</a></p>` : ""}
                ${plugin.stargazers_count ? `<span class="badge badge-stars">⭐ ${plugin.stargazers_count}</span>` : ""}
            `;

            container.appendChild(card);
        });

    } catch (error) {
        console.error('Error fetching plugin data:', error);
        const container = document.getElementById("plugin-container");
        if (container) {
            container.innerHTML = '<p class="text-red-500">❌ Could not load plugin metadata, please try again later.</p>';
        }
    }
}

// Use `document$` to ensure scripts run on page load and after AJAX navigation
document$.subscribe(() => {
    if (document.getElementById("plugin-container")) {
        // console.log("🔄 Detected page change - Reloading plugins...");
        loadPlugins();
    }
});
