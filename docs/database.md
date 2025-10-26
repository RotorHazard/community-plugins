---
id: plugins
title: All Community Plugins
description: Browse all plugins in the Community Database
hide:
  - navigation
  - toc
  - footer
---

# Browse in the Community Plugins Database

<div id="search-bar-container">
  <div class="search-bar-wrapper">
    <input type="text" id="search" placeholder="Search plugins by name, author, description..." />
    <button id="clear-search" class="clear-btn" style="display: none;">×</button>
  </div>
  <div class="filter-dropdown-wrapper">
    <select id="category" class="modern-select">
      <option value="">All Categories</option>
    </select>
  </div>
  <div class="sort-dropdown-wrapper">
    <select id="sort" class="modern-select">
      <option value="latest">⏱️ Latest</option>
      <option value="name">🔤 A-Z</option>
      <option value="stars">⭐ Stars</option>
      <option value="forks">🍴 Forks</option>
    </select>
  </div>
</div>

<div id="results-info"></div>

<div id="plugin-container">
  <p>Loading all plugins...</p>
</div>

<!-- Load scripts -->
<link rel="stylesheet" href="../assets/css/plugin-cards.css">
<link rel="stylesheet" href="../assets/css/styles.css">
<script src="../assets/js/plugins.js" defer></script>
