# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
pagesdir = join_paths(pkgdatadir, 'src/pages')

sources = [
  '__init__.py',
  'details_page.py',
  'edit_episode_page.py',
]

install_data(sources, install_dir: pagesdir)
