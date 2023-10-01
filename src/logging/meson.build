# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
loggingdir = join_paths(pkgdatadir, 'src/logging')

sources = [
  '__init__.py',
  'session_file_handler.py',
]

install_data(sources, install_dir: loggingdir)
