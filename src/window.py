# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gio, GLib, Gtk

from .widgets.theme_switcher import ThemeSwitcher


@Gtk.Template(resource_path='/me/iepure/ticketbooth/ui/window.ui')
class TicketboothWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'TicketboothWindow'

    _stack = Gtk.Template.Child()
    _menu_btn = Gtk.Template.Child()

    _settings = Gio.Settings(schema_id='me.iepure.ticketbooth')

    def _sort_on_changed(self, new_state, source):
        self.set_state(new_state)
        Gio.Settings(schema_id='me.iepure.ticketbooth').set_string('view-sorting', str(new_state)[1:-1])

    def _style_on_changed(self, new_state, source):
        self.set_state(new_state)
        Gio.Settings(schema_id='me.iepure.ticketbooth').set_string('view-style', str(new_state)[1:-1])

    _actions = {
        ('view-sorting', None, 's', f"'{_settings.get_string('view-sorting')}'", _sort_on_changed),
        ('view-style', None, 's', f"'{_settings.get_string('view-style')}'", _style_on_changed),
    }

    def __init__(self, debug,  **kwargs):
        super().__init__(**kwargs)
        self._restore_settings()
        self.add_action_entries(self._actions, self)

        if debug == 'True':
            self.add_css_class('devel')

        # Theme switcher (Adapted from https://gitlab.gnome.org/tijder/blueprintgtk/)
        self._menu_btn.get_popover().add_child(ThemeSwitcher(), 'themeswitcher')

    def _restore_settings(self):
        self._settings.bind('win-width', self, 'default-width', Gio.SettingsBindFlags.DEFAULT)
        self._settings.bind('win-height', self, 'default-height', Gio.SettingsBindFlags.DEFAULT)
        self._settings.bind('win-maximized', self, 'maximized', Gio.SettingsBindFlags.DEFAULT)
        self._settings.bind('win-tab', self._stack, 'visible-child-name', Gio.SettingsBindFlags.DEFAULT)
