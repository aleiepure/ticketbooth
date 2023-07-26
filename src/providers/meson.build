# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
providersdir = join_paths(pkgdatadir, 'src/providers')

sources = [
  '__init__.py',
  'tmdb_provider.py',
  'local_provider.py',
]

install_data(sources, install_dir: providersdir)
