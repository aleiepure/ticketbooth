# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
dialogsdir = join_paths(pkgdatadir, 'src/dialogs')

sources = [
  '__init__.py',
  'add_manual_dialog.py',
  'add_tmdb_dialog.py',
  'edit_season_dialog.py',
]

install_data(sources, install_dir: dialogsdir)
