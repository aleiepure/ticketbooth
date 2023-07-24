# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import glob
import os

from gi.repository import Adw, Gio, GLib, GObject, Gtk

from . import shared  # type: ignore


@Gtk.Template(resource_path=shared.PREFIX + '/ui/preferences.ui')
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = 'PreferencesWindow'

    def __init__(self):
        super().__init__()

    @Gtk.Template.Callback('_on_clear_cache_btn_clicked')
    def _on_clear_cache_btn_clicked(self, user_data: GObject.GPointer):
        files = glob.glob('poster-*.jpg', root_dir=GLib.get_tmp_dir())
        for file in files:
            os.remove(GLib.get_tmp_dir() + '/' + file)
