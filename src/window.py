# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import glob
import logging
import os
from gettext import gettext as _
from gettext import pgettext as C_

from gi.repository import Adw, Gio, GLib, Gtk

from . import shared  # type: ignore
from .background_queue import BackgroundQueue
from .dialogs.add_manual_dialog import AddManualDialog
from .dialogs.add_tmdb_dialog import AddTMDBDialog
from .views.first_run_view import FirstRunView
from .views.db_update_view import DbUpdateView
from .views.main_view import MainView
from .providers.local_provider import LocalProvider as local


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
        logging.debug(f'Sort: {new_state}')
        shared.schema.set_string('view-sorting', str(new_state)[1:-1])

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
        logging.info('Add from TMDB dialog open')
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
        logging.info('Add manual dialog open')
        dialog.present()

    def _refresh(self, new_state: None, source: Gtk.Widget) -> None:
        """
        Callback for the win.refresh action

        Args:
            new_state (None): stateless action, always None
            source (Gtk.Widget): widget that caused the activation

        Returns:
            None
        """

        logging.info('Refresh requested')
        source._win_stack.get_child_by_name('main').refresh()

    def _update_background_indicator(self, new_state: None, source: Gtk.Widget) -> None:
        """
        Callback for the win.update-background-indicator

        Args:
            new_state (None): stateless action, always None
            source (Gtk.Widget): widget that caused the activation

        Returns:
            None
        """

        source._win_stack.get_child_by_name(
            'main')._background_indicator.refresh()

    def _unwatched_first_changed(self, new_state: GLib.Variant, source: Gtk.Widget) -> None:
        """
        Callback for the win.unwatched-first action

        Args:
            new_state (bool): new selected state
            source (Gtk.Widget): widget that caused the activation

        Returns:
            None
        """

        logging.debug(f'Sort unwatched first: {new_state.get_boolean()}')
        shared.schema.set_boolean('unwatched-first', new_state.get_boolean())
        self.set_state(new_state)

    def _separate_watched_changed(self, new_state: GLib.Variant, source: Gtk.Widget) -> None:
        """
        Callback for the win.separate-watched action

        Args:
            new_state (bool): new selected state
            source (Gtk.Widget): widget that caused the activation

        Returns:
            None
        """

        logging.debug(f'Separate watched: {new_state.get_boolean()}')
        shared.schema.set_boolean('separate-watched', new_state.get_boolean())
        self.set_state(new_state)

    def _hide_watched_changed(self, new_state: GLib.Variant, source: Gtk.Widget) -> None:
        """
        Callback for the win.hide-watched action

        Args:
            new_state (bool): new selected state
            source (Gtk.Widget): widget that caused the activation

        Returns:
            None
        """

        logging.debug(f'Hide watched: {new_state.get_boolean()}')
        shared.schema.set_boolean('hide-watched', new_state.get_boolean())
        self.set_state(new_state)

    _actions = {
        ('view-sorting', None, 's',
         f"'{shared.schema.get_string('view-sorting')}'", _sort_on_changed),
        ('separate-watched', None, None, 'true' if shared.schema.get_boolean(
            'separate-watched') else 'false', _separate_watched_changed),
        ('hide-watched', None, None, 'true' if shared.schema.get_boolean('hide-watched')
         else 'false', _hide_watched_changed),
        ('add-tmdb', _add_tmdb),
        ('add-manual', _add_manual),
        ('refresh', _refresh),
        ('update-backgroud-indicator', _update_background_indicator)
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_action_entries(self._actions, self)
        self._restore_state()
        self.app = kwargs.get("application")
        if shared.DEBUG:
            self.add_css_class('devel')

        shared.schema.bind('offline-mode', self.lookup_action('add-tmdb'),
                           'enabled', Gio.SettingsBindFlags.INVERT_BOOLEAN)
        shared.schema.bind('separate-watched', self.lookup_action('hide-watched'),
                           'enabled', Gio.SettingsBindFlags.INVERT_BOOLEAN)

        if shared.schema.get_boolean('onboard-complete'):
            Gio.NetworkMonitor.get_default().connect(
                'network-changed', self._on_network_changed)

    @Gtk.Template.Callback('_on_close_request')
    def _on_close_request(self, user_data: object | None) -> bool:
        """
        Callback for "close-request" signal.
        Checks for background activities to prevent quiting and corruption, deletes cached data if enabled in settings.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            True to block quiting, False to allow it
        """

        logging.info('Close requested')

        # Background activities
        if not all(activity.completed for activity in BackgroundQueue.get_queue()):
            dialog = Adw.MessageDialog.new(self,
                                           C_('message dialog heading',
                                              'Background Activies Running'),
                                           C_('message dialog body', 'Some activities are running in the background and need to be completed before exiting. Look for the indicator in the header bar to check when they are finished.'))
            dialog.add_response('ok', C_('message dialog action', 'OK'))
            dialog.show()
            logging.error('Close inhibited, running activities in background')
            return True

        # Cache
        if shared.schema.get_boolean('exit-remove-cache'):
            files = glob.glob('*.jpg', root_dir=shared.cache_dir)
            for file in files:
                os.remove(shared.cache_dir / file)
            logging.info('Cache deleted')

        # recent_change reset
        local.reset_recent_change()
        logging.info('recent_change reseted')
        logging.info('Closing')
        return False

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, widget: Gtk.Widget) -> None:
        """
        Callback for the "map" signal. Determines what view to show on startup.

        Args:
            widget (Gtk.Widget): the object which received the signal

        Returns:
            None
        """

        is_first_run = shared.schema.get_boolean('first-run')
        logging.info(f'is first run: {is_first_run}')
        if is_first_run:
            logging.info('Start first run setup')
            self.first_run_view = FirstRunView()
            self._win_stack.add_named(child=self.first_run_view, name='first-run')
            self._win_stack.set_visible_child_name('first-run')
            self.first_run_view.connect('exit', self._on_first_run_exit)
            shared.schema.set_boolean('db-needs-update', False)
            return
            
        db_needs_update = shared.schema.get_boolean('db-needs-update')
        if db_needs_update:
            logging.info('Start db update')
            self.db_update_view = DbUpdateView()
            self._win_stack.add_named(child=self.db_update_view, name='db-update')
            self._win_stack.set_visible_child_name('db-update')
            self.db_update_view.connect('exit', self._on_db_update_exit)
            return
            
        self._win_stack.add_named(child=MainView(self), name='main')
        self._win_stack.set_visible_child_name('main')
        return

    def _on_network_changed(self, network_monitor: Gio.NetworkMonitor, network_available: bool) -> None:
        """
        Callback for "network-changed" signal.
        If no network is available, it turns on offline mode.

        Args:
            network_monitor (Gio.NetworkMonitor): the NetworkMonitor in use
            network_available (bool): whether or not the network is available

        Returns:
            None
        """

        logging.warning(f'Network changed, current status {network_available}')
        logging.warning(f'Offline mode: {not network_available}')

        shared.schema.set_boolean(
            'offline-mode', GLib.Variant.new_boolean(not network_available))

    def _on_first_run_exit(self, source: Gtk.Widget) -> None:
        """
        Callback for the "exit" signal. Changes the visible view.

        Args:
            None

        Returns:
            None
        """

        logging.info('First setup done')
        self._win_stack.add_named(child=MainView(self), name='main')
        self._win_stack.set_visible_child_name('main')

    def _on_db_update_exit(self, source: Gtk.Widget) -> None:
        """
        Callback for the "exit" of the db_update task. Changes the visible view.

        Args:
            None

        Returns:
            None
        """

        logging.info('Database Update done')
        self._win_stack.add_named(child=MainView(self), name='main')
        self._win_stack.set_visible_child_name('main')

    def _restore_state(self) -> None:
        """
        Restores the last known state of the window between runs.

        Args:
            None

        Returns:
            None
        """

        shared.schema.bind('win-width', self, 'default-width',
                           Gio.SettingsBindFlags.DEFAULT)
        shared.schema.bind('win-height', self, 'default-height',
                           Gio.SettingsBindFlags.DEFAULT)
        shared.schema.bind('win-maximized', self, 'maximized',
                           Gio.SettingsBindFlags.DEFAULT)
