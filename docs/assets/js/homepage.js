window.numberOfPlugins = window.numberOfPlugins || 6;

async function showLatestPlugins() {
    const container = document.getElementById("plugin-container");
    if (!container) return;

    container.innerHTML = "<p>Loading latest plugins...</p>";

    const plugins = await fetchPluginData();
    if (plugins.length === 0) {
        container.innerHTML = "<p>❌ Could not load latest plugins</p>";
        return;
    }

    // Sorteer en pak de laatste 6
    const latestPlugins = plugins.sort((a, b) => new Date(b.last_updated) - new Date(a.last_updated)).slice(0, window.numberOfPlugins);
    container.innerHTML = ""; // Clear oude content

    latestPlugins.forEach(plugin => {
        const manifest = plugin.manifest;
        const repoUrl = `https://github.com/${plugin.repository}`;

        const card = document.createElement("div");
        card.classList.add("plugin-card");
        card.setAttribute("role", "button");
        card.tabIndex = 0;
        card.onclick = () => window.open(repoUrl, "_blank");

        card.innerHTML = `
            <span class="version-badge">${manifest.version}</span>
            <h2>${manifest.name}</h2>
            <p class="plugin-description">${manifest.description}</p>
            <p><strong>Author:</strong> <a href="${manifest.author_uri}" target="_blank">${manifest.author}</a></p>
        `;

        container.appendChild(card);
    });
}

// ✅ Voer uit wanneer MkDocs Material een pagina laadt
document$.subscribe(() => {
    if (document.getElementById("plugin-container")) {
        showLatestPlugins();
    }
});
