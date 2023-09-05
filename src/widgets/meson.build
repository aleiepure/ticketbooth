# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
widgetsdir = join_paths(pkgdatadir, 'src/widgets')

sources = [
  '__init__.py',
  'theme_switcher.py',
  'poster_button.py',
  'search_result_row.py',
  'episode_row.py',
  'image_selector.py',
  'season_expander.py',
  'background_indicator.py',
  'background_activity_row.py',
]

install_data(sources, install_dir: widgetsdir)
