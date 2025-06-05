// Ensure global variables are only declared once
window.allPlugins = window.allPlugins || [];
window.currentPage = window.currentPage || 1;
window.itemsPerPage = window.itemsPerPage || 12;
window.observer = window.observer || null;

async function showAllPlugins() {
    const container = document.getElementById("plugin-container");
    const categorySelect = document.getElementById("category");
    const sortSelect = document.getElementById("sort");

    if (!container || !categorySelect || !sortSelect) {
        // console.warn("⚠️ Skipping plugin loading: Not on database page.");
        return;
    }

    container.innerHTML = "<p>Loading all plugins...</p>";

    const plugins = await fetchPluginData((freshPlugins) => {
        window.allPlugins = freshPlugins;
        populateCategories(freshPlugins);
        renderPlugins();
    }, true);

    if (!plugins || plugins.length === 0) {
        container.innerHTML = "<p>❌ Unable to load plugins.</p>";
        return;
    }

    // Store plugins globally
    window.allPlugins = plugins;

    // Populate categories **after** plugins are fetched
    populateCategories(plugins);

    // Render plugins immediately after fetching data
    renderPlugins();
}

// Populate the category dropdown from all unique categories
function populateCategories(plugins) {
    const categorySelect = document.getElementById("category");
    if (!categorySelect) return;

    const categories = new Set();
    let hasUncategorized = false;
    plugins.forEach(plugin => {
        if (Array.isArray(plugin.categories) && plugin.categories.length > 0) {
            plugin.categories.forEach(cat => categories.add(cat));
        } else {
            hasUncategorized = true;
        }
    });

    categorySelect.innerHTML = '<option value="">All Categories</option>';
    Array.from(categories).sort().forEach(cat => {
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

    // console.log("✅ Categories populated:", Array.from(categories));
}

// Function to get the latest release date
function getLatestReleaseDate(plugin) {
    return new Date(plugin.releases[0].published_at);
}

// Render plugins with filtering, sorting, and lazy loading
function renderPlugins() {
    const container = document.getElementById("plugin-container");
    const categorySelect = document.getElementById("category");
    const sortSelect = document.getElementById("sort");

    if (!container || !categorySelect || !sortSelect) {
        // console.warn("⚠️ Skipping render: Missing required elements.");
        return;
    }

    container.innerHTML = "";

    const searchQuery = document.getElementById("search")?.value?.toLowerCase() || "";
    const selectedCategory = categorySelect.value;
    const sortType = sortSelect.value;

    let filteredPlugins = window.allPlugins.filter(plugin => {
        let matchesCategory = true;
        if (selectedCategory) {
            if (selectedCategory === "__uncategorized__") {
                matchesCategory = plugin.categories.length === 0;
            } else {
                matchesCategory = plugin.categories && plugin.categories.includes(selectedCategory);
            }
        }
        const manifest = plugin.manifest;
        const matchesSearch = manifest.name.toLowerCase().includes(searchQuery) ||
            (manifest.description && manifest.description.toLowerCase().includes(searchQuery));
        return matchesCategory && matchesSearch;
    });

    // console.log("🔍 Filtering by category:", selectedCategory, filteredPlugins.length);

    // Sorting logic
    if (sortType === "latest") {
        filteredPlugins.sort((a, b) => getLatestReleaseDate(b) - getLatestReleaseDate(a));
    } else if (sortType === "name") {
        filteredPlugins.sort((a, b) => a.manifest.name.localeCompare(b.manifest.name));
    } else if (sortType === "stars") {
        filteredPlugins.sort((a, b) => (b.stargazers_count || 0) - (a.stargazers_count || 0));
    } else if (sortType === "forks") {
        filteredPlugins.sort((a, b) => (b.forks_count || 0) - (a.forks_count || 0));
    }

    // Lazy load per page
    const startIndex = (window.currentPage - 1) * window.itemsPerPage;
    const visiblePlugins = filteredPlugins.slice(0, startIndex + window.itemsPerPage);

    if (visiblePlugins.length === 0) {
        container.innerHTML = "<p>No plugins found for this filter.</p>";
        return;
    }

    visiblePlugins.forEach(plugin => {
        const manifest = plugin.manifest;
        const repoUrl = `https://github.com/${plugin.repository}`;
        const starCount = plugin.stargazers_count || 0;
        const forkCount = plugin.forks_count || 0;

        const card = document.createElement("div");
        card.classList.add("plugin-card");
        card.setAttribute("role", "button");
        card.tabIndex = 0;

        card.onclick = (e) => {
            if (e.target.closest("a")) return;
            window.open(repoUrl, "_blank");
        };

        card.innerHTML = `
            <span class="version-badge">${manifest.version}</span>
            <h2>${manifest.name}</h2>
            <p class="plugin-description">${manifest.description}</p>
            <p><strong>Author:</strong> ${
                manifest.author_uri
                    ? `<a href="${manifest.author_uri}" target="_blank">${manifest.author}</a>`
                    : manifest.author
            }</p>
            <div class="plugin-footer">
                <div class="footer-left">
                    ${
                        plugin.categories.length > 0
                        ? plugin.categories.map(cat => `<span class="badge badge-category">${cat}</span>`).join(" ")
                        : `<span class="badge badge-uncategorized">Uncategorized</span>`
                    }
                </div>
                <div class="footer-right">
                    ${starCount > 0 ? `<span class="badge badge-stars" title="${starCount} stars">⭐ ${starCount}</span>` : ""}
                    ${forkCount > 0 ? `<span class="badge badge-forks" title="${forkCount} forks">🍴 ${forkCount}</span>` : ""}
                </div>
            </div>
        `;

        container.appendChild(card);
    });
}

// Detect scrolling for lazy loading
function handleScroll() {
    const scrollY = window.scrollY + window.innerHeight;
    const docHeight = document.documentElement.scrollHeight;

    if (scrollY >= docHeight - 200) {
        window.currentPage++;
        renderPlugins();
    }
}

// Handle MkDocs page navigation
document$.subscribe(() => {
    if (document.getElementById("plugin-container")) {
        // console.log("✅ Detected plugins page, loading plugins...");
        showAllPlugins();

        // Start observing mutations to detect navigation away from the page
        window.observer = new MutationObserver(() => {
            if (!document.getElementById("plugin-container")) {
                // console.log("🚨 Left plugins page, cleaning up...");
                cleanupEventListeners();
            }
        });

        window.observer.observe(document.body, { childList: true, subtree: true });

        // Add scroll listener for lazy loading
        window.addEventListener("scroll", handleScroll);
    } else {
        // console.log("🚫 Not on plugins page, skipping initialization.");
    }
});

// Remove event listeners when leaving plugins page
function cleanupEventListeners() {
    window.removeEventListener("scroll", handleScroll);
    if (window.observer) window.observer.disconnect();
}

// Update plugins when filter or sort changes
document.addEventListener("input", (event) => {
    if (["sort", "category", "search"].includes(event.target.id)) {
        window.currentPage = 1;
        renderPlugins();
    }
});
