# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
widgetsdir = join_paths(pkgdatadir, 'ticketbooth/widgets')

sources = [
  '__init__.py',
  'theme_switcher.py',
]

install_data(sources, install_dir: widgetsdir)
