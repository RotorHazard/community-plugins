// Global variables
window.allPlugins = window.allPlugins || [];
window.currentPage = window.currentPage || 1;
window.itemsPerPage = window.itemsPerPage || 12;
window.observer = window.observer || null;

/**
 * Fetch and display all plugins in the database view.
 */
async function showAllPlugins() {
    const container = document.getElementById("plugin-container");
    const categorySelect = document.getElementById("category");
    const sortSelect = document.getElementById("sort");

    if (!container || !categorySelect || !sortSelect) return;

    container.innerHTML = "<p>Loading all plugins...</p>";

    const plugins = await fetchPluginData();

    if (!plugins.length) {
        container.innerHTML = "<p>❌ Unable to load plugins.</p>";
        return;
    }

    window.allPlugins = plugins;
    window.currentPage = 1;

    populateCategories(plugins);
    renderPlugins();
}

/**
 * Populates the category dropdown with unique categories from the plugins.
 */
function populateCategories(plugins) {
    const categorySelect = document.getElementById("category");
    if (!categorySelect) return;

    const categories = new Set();
    let hasUncategorized = false;

    plugins.forEach(plugin => {
        if (plugin.categories.length > 0) {
            plugin.categories.forEach(cat => categories.add(cat));
        } else {
            hasUncategorized = true;
        }
    });

    categorySelect.innerHTML = '<option value="">All Categories</option>';
    [...categories].sort().forEach(cat => {
        const option = document.createElement("option");
        option.value = cat;
        option.textContent = cat;
        categorySelect.appendChild(option);
    });

    if (hasUncategorized) {
        const uncategorized = document.createElement("option");
        uncategorized.value = "__uncategorized__";
        uncategorized.textContent = "Uncategorized";
        categorySelect.appendChild(uncategorized);
    }
}

/**
 * Renders the plugin list with filtering, sorting, and lazy loading.
 */
function renderPlugins() {
    const container = document.getElementById("plugin-container");
    const categorySelect = document.getElementById("category");
    const sortSelect = document.getElementById("sort");
    const search = document.getElementById("search");

    if (!container || !categorySelect || !sortSelect) return;

    const query = search?.value?.toLowerCase() || "";
    const selectedCategory = categorySelect.value;
    const sortBy = sortSelect.value;

    let filtered = window.allPlugins.filter(plugin => {
        const manifest = plugin.manifest;

        const matchesCategory = selectedCategory
            ? selectedCategory === "__uncategorized__"
                ? plugin.categories.length === 0
                : plugin.categories.includes(selectedCategory)
            : true;

        const matchesSearch = [manifest.name, manifest.description, manifest.author]
            .filter(Boolean)
            .some(field => field.toLowerCase().includes(query));

        return matchesCategory && matchesSearch;
    });

    if (sortBy === "latest") {
        filtered.sort((a, b) => new Date(b.releases?.[0]?.published_at || 0) - new Date(a.releases?.[0]?.published_at || 0));
    } else if (sortBy === "name") {
        filtered.sort((a, b) => a.manifest.name.localeCompare(b.manifest.name));
    } else if (sortBy === "stars") {
        filtered.sort((a, b) => (b.stargazers_count || 0) - (a.stargazers_count || 0));
    } else if (sortBy === "forks") {
        filtered.sort((a, b) => (b.forks_count || 0) - (a.forks_count || 0));
    }

    const start = (window.currentPage - 1) * window.itemsPerPage;
    const visible = filtered.slice(0, start + window.itemsPerPage);

    container.innerHTML = visible.length
        ? ""
        : "<p>No plugins found for this filter.</p>";

    visible.forEach(plugin => renderPluginCard(plugin, container));
}

/**
 * Generates and appends a plugin card to the container.
 */
function renderPluginCard(plugin, container) {
    const manifest = plugin.manifest;
    const repoUrl = `https://github.com/${plugin.repository}`;
    const starCount = plugin.stargazers_count || 0;
    const forkCount = plugin.forks_count || 0;
    const releaseDate = plugin.releases?.[0]?.published_at
        ? new Date(plugin.releases[0].published_at).toLocaleDateString()
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
            <div class="footer-right">
                ${starCount ? `<span class="badge badge-stars" title="${starCount} stars">⭐ ${starCount}</span>` : ""}
                ${forkCount ? `<span class="badge badge-forks" title="${forkCount} forks">🍴 ${forkCount}</span>` : ""}
            </div>
        </div>
    `;

    container.appendChild(card);
}

/**
 * Scroll handler voor lazy loading.
 */
function handleScroll() {
    const scrollY = window.scrollY + window.innerHeight;
    const docHeight = document.documentElement.scrollHeight;

    if (scrollY >= docHeight - 200) {
        window.currentPage++;
        renderPlugins();
    }
}

/**
 * Cleanup of event listeners when leaving the page.
 */
function cleanupEventListeners() {
    window.removeEventListener("scroll", handleScroll);
    if (window.observer) window.observer.disconnect();
}

/**
 * Init when navigating to the plugin page (via MkDocs).
 */
document$.subscribe(() => {
    const onPluginPage = document.getElementById("plugin-container");
    if (!onPluginPage) return;

    showAllPlugins();

    window.observer = new MutationObserver(() => {
        if (!document.getElementById("plugin-container")) {
            cleanupEventListeners();
        }
    });

    window.observer.observe(document.body, { childList: true, subtree: true });
    window.addEventListener("scroll", handleScroll);
});

/**
 * Filters or sorting options change → re-render.
 */
document.addEventListener("input", (event) => {
    if (["sort", "category", "search"].includes(event.target.id)) {
        window.currentPage = 1;
        renderPlugins();
    }
});
