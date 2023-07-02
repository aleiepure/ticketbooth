# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'ticketbooth')
gnome = import('gnome')

# Compile resources
blueprints = custom_target('blueprints',
  input: files(
    'ui/gtk/help-overlay.blp',
    'ui/window.blp',
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@']
)

gnome.compile_resources('ticketbooth',
  'ticketbooth.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: blueprints
)


# Debug info
if get_option('debug')
  name_suffix = ' (Development snapshot)'

  git = find_program('git', required : false)
  if git.found()
    git_commit = run_command('git', 'rev-parse', '--short', 'HEAD', check:false).stdout().strip()
  endif

  if git_commit == ''
    version_number = '-Devel'
  else
    version_number = 'Git-@0@'.format(git_commit)
  endif

else
  name_suffix = ''
  version_number = meson.project_version()
endif


# Python setup
python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', version_number)
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)
conf.set('debug', get_option('debug'))
conf.set('app-name', 'Ticket Booth@0@'.format(name_suffix))

configure_file(
  input: 'ticketbooth.in',
  output: 'ticketbooth',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)


# Install sources
ticketbooth_sources = [
  '__init__.py',
  'main.py',
  'window.py',
]

install_data(ticketbooth_sources, install_dir: moduledir)
