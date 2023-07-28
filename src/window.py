# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gio, Gtk

from . import shared  # type: ignore
from .dialogs.add_manual_dialog import AddManualDialog
from .dialogs.add_tmdb_dialog import AddTMDBDialog
from .views.first_run_view import FirstRunView
from .views.main_view import MainView


@Gtk.Template(resource_path=shared.PREFIX + '/ui/window.ui')
class TicketboothWindow(Adw.ApplicationWindow):
    """
    This class reppresents the main application window.

    Properties:
        None

    Methods:
        None

    Signals:
        None
    """

    __gtype_name__ = 'TicketboothWindow'

    _win_stack = Gtk.Template.Child()

    def _sort_on_changed(self, new_state: str, source: Gtk.Widget) -> None:
        """
        Callback for the win.view-sorting action

        Args:
            new_state (str): new selected state
            source (Gtk.Widget): widget that caused the activation

        Returns:
            None
        """

        self.set_state(new_state)
        shared.schema.set_string('view-sorting', str(new_state)[1:-1])

    def _style_on_changed(self, new_state: str, source: Gtk.Widget) -> None:
        """
        Callback for the win.view-style action

        Args:
            new_state (str): new selected state
            source (Gtk.Widget): widget that caused the activation

        Returns:
            None
        """

        self.set_state(new_state)
        shared.schema.set_string('view-style', str(new_state)[1:-1])

    def _add_tmdb(self, new_state: None, source: Gtk.Widget) -> None:
        """
        Callback for the win.add-tmdb action

        Args:
            new_state (None): stateless action, always None
            source (Gtk.Widget): widget that caused the activation

        Returns:
            None
        """

        dialog = AddTMDBDialog(source)
        dialog.connect('close-request', lambda data: source._win_stack.get_child_by_name('main').refresh())
        dialog.present()

    def _add_manual(self, new_state: None, source: Gtk.Widget) -> None:
        """
        Callback for the win.add-manual action

        Args:
            new_state (None): stateless action, always None
            source (Gtk.Widget): widget that caused the activation

        Returns:
            None
        """

        dialog = AddManualDialog(source)
        dialog.connect('close-request', lambda data: source._win_stack.get_child_by_name('main').refresh())
        dialog.present()

    _actions = {
        ('view-sorting', None, 's', f"'{shared.schema.get_string('view-sorting')}'", _sort_on_changed),
        ('view-style', None, 's', f"'{shared.schema.get_string('view-style')}'", _style_on_changed),
        ('add-tmdb', _add_tmdb),
        ('add-manual', _add_manual),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_action_entries(self._actions, self)
        self._restore_state()

        if shared.DEBUG:
            self.add_css_class('devel')

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, widget: Gtk.Widget) -> None:
        """
        Callback for the "map" signal. Determines what view to show on startup.

        Args:
            widget (Gtk.Widget): the object which received the signal

        Returns:
            None
        """

        if not shared.schema.get_boolean('first-run'):
            self._win_stack.add_named(child=MainView(), name='main')
            self._win_stack.set_visible_child_name('main')
            return

        self.first_run_view = FirstRunView()
        self._win_stack.add_named(child=self.first_run_view, name='first-run')
        self._win_stack.set_visible_child_name('first-run')
        self.first_run_view.connect('exit', self._on_first_run_exit)

    def _on_first_run_exit(self, source: Gtk.Widget) -> None:
        """
        Callback for the "exit" signal. Changes the visible view.

        Args:
            None

        Returns:
            None
        """

        self._win_stack.add_named(child=MainView(), name='main')
        self._win_stack.set_visible_child_name('main')

    def _restore_state(self) -> None:
        """
        Restores the last known state of the window between runs.

        Args:
            None

        Returns:
            None
        """

        shared.schema.bind('win-width', self, 'default-width', Gio.SettingsBindFlags.DEFAULT)
        shared.schema.bind('win-height', self, 'default-height', Gio.SettingsBindFlags.DEFAULT)
        shared.schema.bind('win-maximized', self, 'maximized', Gio.SettingsBindFlags.DEFAULT)
