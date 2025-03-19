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

    // Sort plugins by latest release published
    const latestPlugins = plugins.sort((a, b) => new Date(b.releases[0].published_at) - new Date(a.releases[0].published_at)).slice(0, window.numberOfPlugins);
    container.innerHTML = ""; // Clear oude content

    latestPlugins.forEach(plugin => {
        const manifest = plugin.manifest;
        const repoUrl = `https://github.com/${plugin.repository}`;
        const releaseDate = new Date(plugin.releases[0].published_at).toLocaleDateString();

        const card = document.createElement("div");
        card.classList.add("plugin-card");
        card.setAttribute("role", "button");
        card.tabIndex = 0;
        card.onclick = () => window.open(repoUrl, "_blank");

        card.innerHTML = `
            <span class="version-badge">${manifest.version}</span>
            <h2>${manifest.name}</h2>
            <p class="plugin-description">${manifest.description}</p>
            <p class="release-date"><strong>Released:</strong> ${releaseDate}</p>
            <p><strong>Author:</strong> <a href="${manifest.author_uri}" target="_blank">${manifest.author}</a></p>
        `;

        container.appendChild(card);
    });
}

// Run when MkDocs Material loads a page
document$.subscribe(() => {
    if (document.getElementById("plugin-container")) {
        showLatestPlugins();
    }
});
