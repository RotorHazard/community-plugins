// How many plugins to show on the homepage
window.numberOfPlugins = window.numberOfPlugins || 6;
window.formatDate = window.formatDate || new Intl.DateTimeFormat("default", { dateStyle: "medium" });

/**
 * Fetch and display the latest plugins on the homepage.
 */
async function showLatestPlugins() {
    const container = document.getElementById("plugin-container");
    if (!container) return;

    container.innerHTML = "<p>Loading latest plugins...</p>";

    // Fallback op in-memory cache
    const plugins = window.pluginData?.length ? window.pluginData : await fetchPluginData();

    if (!plugins.length) {
        container.innerHTML = "<p>❌ Could not load latest plugins</p>";
        return;
    }

    updatePluginCountBadge(plugins.length);

    const latestPlugins = plugins
        .filter(p => p.releases?.[0]?.published_at)
        .sort((a, b) => new Date(b.releases[0].published_at) - new Date(a.releases[0].published_at))
        .slice(0, window.numberOfPlugins);

    const fragment = document.createDocumentFragment();
    latestPlugins.forEach(plugin => renderPluginCard(plugin, fragment));
    container.innerHTML = "";
    container.appendChild(fragment);
}

/**
 * Generate and append a plugin card to the container.
 */
function renderPluginCard(plugin, container) {
    const manifest = plugin.manifest;
    const repoUrl = `https://github.com/${plugin.repository}`;
    const releaseDate = plugin.releases?.[0]?.published_at
        ? formatDate.format(new Date(plugin.releases[0].published_at))
        : "Unknown";

    const card = document.createElement("div");
    card.className = "plugin-card";
    card.setAttribute("role", "button");
    card.tabIndex = 0;

    card.onclick = (e) => {
        if (!e.target.closest("a")) {
            window.open(repoUrl, "_blank");
        }
    };

    card.innerHTML = `
        <span class="version-badge">${manifest.version}</span>
        <h2>${manifest.name}</h2>
        <p class="plugin-description">${manifest.description}</p>
        <p class="release-date"><strong>Released:</strong> ${releaseDate}</p>
        <p><strong>Author:</strong> ${
            manifest.author_uri
                ? `<a href="${manifest.author_uri}" target="_blank">${manifest.author}</a>`
                : manifest.author
        }</p>
        <div class="plugin-footer">
            <div class="footer-left">
                ${
                    plugin.categories.length
                        ? plugin.categories.map(cat => `<span class="badge badge-category">${cat}</span>`).join(" ")
                        : `<span class="badge badge-uncategorized">Uncategorized</span>`
                }
            </div>
        </div>
    `;

    container.appendChild(card);
}

/**
 * Show the total number of plugins in the badge (optional).
 */
function updatePluginCountBadge(count) {
    const badge = document.getElementById("plugin-count");
    if (badge) {
        badge.innerHTML = `🚀 ${count} plugins added`;
    }
}

// Run when MkDocs Material loads a page
document$.subscribe(() => {
    if (document.getElementById("plugin-container")) {
        showLatestPlugins();
    }
});
