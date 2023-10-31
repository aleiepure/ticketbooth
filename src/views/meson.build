# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
viewsdir = join_paths(pkgdatadir, 'src/views')

sources = [
  '__init__.py',
  'main_view.py',
  'first_run_view.py',
  'db_update_view.py',
  'content_view.py',
]

install_data(sources, install_dir: viewsdir)
