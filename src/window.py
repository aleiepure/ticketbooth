# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gio, GLib, Gtk

from . import shared  # type: ignore
from .dialogs.add_manual_dialog import AddManualDialog
from .dialogs.add_tmdb_dialog import AddTMDBDialog
from .widgets.theme_switcher import ThemeSwitcher


@Gtk.Template(resource_path=shared.PREFIX + '/ui/window.ui')
class TicketboothWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'TicketboothWindow'

    _stack = Gtk.Template.Child()
    _menu_btn = Gtk.Template.Child()

    def _sort_on_changed(self, new_state, source):
        self.set_state(new_state)
        shared.schema.set_string('view-sorting', str(new_state)[1:-1])

    def _style_on_changed(self, new_state, source):
        self.set_state(new_state)
        shared.schema.set_string('view-style', str(new_state)[1:-1])

    def _add_tmdb(self, new_state, source):
        dialog = AddTMDBDialog(source)
        dialog.present()

    def _add_manual(self, new_state, source):
        dialog = AddManualDialog(source)
        dialog.present()

    _actions = {
        ('view-sorting', None, 's', f"'{shared.schema.get_string('view-sorting')}'", _sort_on_changed),
        ('view-style', None, 's', f"'{shared.schema.get_string('view-style')}'", _style_on_changed),
        ('add-tmdb', _add_tmdb),
        ('add-manual', _add_manual),
    }

    def __init__(self, debug,  **kwargs):
        super().__init__(**kwargs)
        self._restore_state()
        self.add_action_entries(self._actions, self)

        if shared.DEBUG == 'True':
            self.add_css_class('devel')

        # Theme switcher (Adapted from https://gitlab.gnome.org/tijder/blueprintgtk/)
        self._menu_btn.get_popover().add_child(ThemeSwitcher(), 'themeswitcher')

    def _restore_state(self):
        shared.schema.bind('win-width', self, 'default-width', Gio.SettingsBindFlags.DEFAULT)
        shared.schema.bind('win-height', self, 'default-height', Gio.SettingsBindFlags.DEFAULT)
        shared.schema.bind('win-maximized', self, 'maximized', Gio.SettingsBindFlags.DEFAULT)
        shared.schema.bind('win-tab', self._stack, 'visible-child-name', Gio.SettingsBindFlags.DEFAULT)
