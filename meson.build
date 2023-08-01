# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

project('ticketbooth',
          version: '0.1.0',
    meson_version: '>= 0.62.0',
  default_options: [ 'warning_level=2', 'werror=false', ],
)

i18n = import('i18n')
gnome = import('gnome')

# Debug info
if get_option('prerelease')
  name_suffix = ' (Development snapshot)'
  app_id = 'me.iepure.Ticketbooth.Devel'
  prefix = '/me/iepure/Ticketbooth/Devel'

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
  app_id = 'me.iepure.Ticketbooth'
  prefix = '/me/iepure/Ticketbooth'
  version_number = meson.version()
endif


# Python setup
python = import('python')

# Config data
conf = configuration_data()
conf.set('python', python.find_installation('python3').full_path())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', join_paths(get_option('prefix'), get_option('datadir'), meson.project_name()))
conf.set('debug', get_option('prerelease'))
conf.set('app_id', app_id)
conf.set('version', version_number)
conf.set('app_name', 'Ticket Booth@0@'.format(name_suffix))
conf.set('prefix', prefix)

subdir('data')
subdir('src')
subdir('po')

install_data(
  configure_file(
    input: 'install/ticketbooth-run-script.in',
    output: 'ticketbooth-run-script',
    configuration: conf
  ),
  install_dir: join_paths(get_option('prefix'), meson.project_name())
)

gnome.post_install(
     glib_compile_schemas: true,
    gtk_update_icon_cache: true,
  update_desktop_database: true,
)
