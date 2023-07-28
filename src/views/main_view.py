# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gio, GLib, GObject, Gtk

from .. import shared  # type: ignore
from ..widgets.theme_switcher import ThemeSwitcher


@Gtk.Template(resource_path=shared.PREFIX + '/ui/views/main_view.ui')
class MainView(Adw.Bin):
    """
    This class rappresents the main view of the app.

    Properties:
        None

    Methods:
        refresh(): Causes the window to update its contents

    Signals:
        None
    """

    __gtype_name__ = 'MainView'

    _tab_stack = Gtk.Template.Child()
    _menu_btn = Gtk.Template.Child()
    _banner = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

        shared.schema.bind('win-tab', self._tab_stack, 'visible-child-name', Gio.SettingsBindFlags.DEFAULT)
        shared.schema.bind('offline-mode', self._banner, 'revealed', Gio.SettingsBindFlags.GET)

        # Theme switcher (Adapted from https://gitlab.gnome.org/tijder/blueprintgtk/)
        self._menu_btn.get_popover().add_child(ThemeSwitcher(), 'themeswitcher')

    def refresh(self) -> None:
        """
        Refreshes the visible window.

        Args:
            None

        Returns:
            None
        """
        self._tab_stack.get_visible_child().refresh_view()
