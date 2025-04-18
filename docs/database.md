---
id: plugins
title: All Plugins
description: Browse all plugins in the Community Database
hide:
  - navigation
  - toc
  - footer
---

# Browse in the Community Plugins Database

On this page, you can explore all plugins available in the RotorHazard Community Database. Use the filters below to quickly find the plugin you're looking for.

<div id="filter-container">
  <label for="category">Filter by Category:</label>
  <select id="category">
    <option value="">All Categories</option>
  </select>

  <label for="sort">Sort by:</label>
  <select id="sort">
    <option value="latest">Last Updated</option>
    <option value="name">Name (A-Z)</option>
    <option value="stars">Star Count</option>
    <option value="forks">Fork Count</option>
  </select>
</div>

<div id="plugin-container">
  <p>Loading all plugins...</p>
</div>

<!-- Load scripts -->
<link rel="stylesheet" href="../assets/css/styles.css">
<script src="../assets/js/plugins.js" defer></script>
