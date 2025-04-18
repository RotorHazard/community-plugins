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

// Populate the category dropdown dynamically
function populateCategories(plugins) {
    const categorySelect = document.getElementById("category");
    if (!categorySelect) return;

    const categories = new Set();
    plugins.forEach(plugin => {
        if (Array.isArray(plugin.manifest.category)) {
            plugin.manifest.category.forEach(cat => categories.add(cat));
        }
    });

    categorySelect.innerHTML = '<option value="">All Categories</option>';
    categories.forEach(cat => {
        const option = document.createElement("option");
        option.value = cat;
        option.textContent = cat;
        categorySelect.appendChild(option);
    });

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

    container.innerHTML = ""; // Clear previous content

    const sortType = sortSelect.value;
    const selectedCategory = categorySelect.value;

    let filteredPlugins = window.allPlugins.filter(plugin => {
        return !selectedCategory || (plugin.manifest.category && plugin.manifest.category.includes(selectedCategory));
    });

    // console.log("🔍 Filtering by category:", selectedCategory, filteredPlugins.length);

    // Sorting logic
    if (sortType === "latest") {
        filteredPlugins.sort((a, b) => getLatestReleaseDate(b) - getLatestReleaseDate(a));
    } else if (sortType === "name") {
        filteredPlugins.sort((a, b) => a.manifest.name.localeCompare(b.manifest.name));
    } else if (sortType === "stars") {
        filteredPlugins.sort((a, b) => (b.stargazers_count || 0) - (a.stargazers_count || 0));
    }  else if (sortType === "forks") {
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
        card.onclick = () => window.open(repoUrl, "_blank");

        card.innerHTML = `
            <span class="version-badge">${manifest.version}</span>
            <h2>${manifest.name}</h2>
            <p class="plugin-description">${manifest.description}</p>
            <p><strong>Author:</strong> <a href="${manifest.author_uri}" target="_blank">${manifest.author}</a></p>
            <p><strong>Category:</strong> ${manifest.category ? manifest.category.join(', ') : "None"}</p>
            <div class="plugin-footer">
                ${starCount > 0 ? `<span class="badge badge-stars">⭐ ${starCount} Stars</span>` : ""}
                ${forkCount > 0 ? `<span class="badge badge-forks">🍴 ${forkCount} Forks</span>` : ""}
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
    if (event.target.id === "sort" || event.target.id === "category") {
        window.currentPage = 1;
        renderPlugins();
    }
});
