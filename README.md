<div align="center">
  <h1><img src="./data/icons/hicolor/scalable/apps/me.iepure.Ticketbooth.svg" height="64" alt="Ticket Booth Icon"/><br>Ticket Booth (Enhanced)</h1>
  <h4>Keep track of your favorite shows - Maintained & Refactored</h4>
</div>

> [!IMPORTANT]
> **Active Maintenance Fork:** This repository is an enhanced version of the original Ticket Booth. 
> It includes critical architectural fixes, performance optimizations (Widget Recycling), 
> and resolved dependency conflicts (Logging namespace) that are currently pending in the upstream.

<div align="center">
  <a href="https://github.com/void0x14/ticketbooth/actions" title="Build Flatpak status">
    <img src="https://github.com/void0x14/ticketbooth/actions/workflows/build-x86.yaml/badge.svg" alt="CI workflow status"/>
  </a>
  <a href="./LICENSES/GPL-3.0-or-later.txt" title="GPL-3 License">
    <img src="https://img.shields.io/badge/License-GPL--3.0-blue.svg" alt="GPL 3 License">
  </a>
  <a href="https://stopthemingmy.app" title="Please do not theme this app">
    <img src="https://stopthemingmy.app/badge.svg" alt="Please do not theme this app"/>
  </a>
  <br />
  <a href="#enhanced-features">Key Improvements</a> ·
  <a href="#install">Install</a> ·
  <a href="#contribute">Contribute</a> ·
  <a href="#license">License</a>
</div>

## Enhanced Features (by void0x14)

In addition to core functionalities, this fork introduces:

* **Modernized Architecture:** Standardized codebase to English and refactored for better maintainability.
* **Memory Efficiency:** Implemented **Widget Recycling** in `ContentGridView` to prevent memory leaks during heavy scrolling.
* **Logging Fix:** Resolved the critical `logging` namespace conflict that shadowed Python's standard library.
* **Security:** Audited and enforced parameterized SQL queries to prevent potential injection.
* **UI Fluidity:** Integrated chunked data loading for a smoother experience with large libraries.

## Core Features

Ticket Booth allows you to build your watchlist of movies and TV Shows, keep track of watched titles, and find information about the latest releases.

*Ticket Booth does not allow you to watch or download content. This app uses the TMDB API but is not endorsed or certified by TMDB.*

## Install

Builds from the main branch are available as artifacts on the [Actions page](https://github.com/void0x14/ticketbooth/actions).\
To build from source, see [Building](./CONTRIBUTING.md#building).

## Contribute

Since this is an active development fork, issues and pull requests are welcome here! If you've found a bug or have a feature request that is ignored in the upstream, feel free to open an issue in this repository.

See [Contributing](./CONTRIBUTING.md) to learn more.

## License

Copyright (C) 2023-2025 Alessandro Iepure
Copyright (C) 2026 void0x14 (Fork Maintenance)

This application comes with absolutely no warranty. See the GNU General Public
License, version 3 or later for details. A [copy of the license](./LICENSES/GPL-3.0-or-later.txt)
can be found in the [LICENSES/](./LICENSES/) folder.
