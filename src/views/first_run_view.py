# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import locale
import logging
import os
from gettext import gettext as _

from gi.repository import Adw, Gio, GLib, GObject, Gtk

from .. import shared  # type: ignore
from ..models.language_model import LanguageModel
from ..providers.local_provider import LocalProvider as local
from ..providers.tmdb_provider import TMDBProvider as tmdb


@Gtk.Template(resource_path=shared.PREFIX + '/ui/views/first_run_view.ui')
class FirstRunView(Adw.Bin):
    """
    This class represents the initial setup the app needs to offer full fuctionality.

    Properties:
        None

    Methods:
        None

    Signals:
        exit: emited when the view has completed its operations, either the required data was successfully downloaded \
              or the user requested "offline mode"
    """

    __gtype_name__ = 'FirstRunView'

    _heading_lbl = Gtk.Template.Child()
    _status_lbl = Gtk.Template.Child()
    _offline_btn = Gtk.Template.Child()
    _retry_check_btn = Gtk.Template.Child()

    __gsignals__ = {
        'exit': (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    _cancellable = Gio.Cancellable.new()

    def __init__(self):
        super().__init__()

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data: object | None) -> None:
        """
        Callback for "map" signal.
        Creates the directories and tables in the local db, sets the tmdb results language based on the locale, and attempts to download required data if connected to the Internet.

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        logging.info('First run setup in progress...')

        for path in [shared.background_dir, shared.poster_dir, shared.series_dir]:
            if not os.path.exists(path):
                os.makedirs(path)
                logging.info(f'[setup] Created folder {path}')

        local.create_tables()
        logging.info('[setup] Created db tables')

        language = locale.getdefaultlocale()[0].lower()[:2]  # type: ignore
        shared.schema.set_string('tmdb-lang', language)
        logging.info(f'[Setup] Set TMDB language to {language}')

        self._update_ui(need_download=True)
        Gio.NetworkMonitor.get_default().can_reach_async(
            Gio.NetworkAddress.parse_uri('https://api.themoviedb.org', 80),
            self._cancellable,
            self._on_first_reach_done,
            None
        )
        logging.info('[Setup] Checking network connection...')

    def _update_ui(self, need_download: bool) -> None:
        """
        Updates the UI strings to reflect its state:
            - if need_download is TRUE, the UI tells the user that the Internet is needed and some data will be
              downloaded. Additionally it shows options to proceed offline.
            - if need_download is FALSE, the UI tells the user a generic message.

        Args:
            need_download (bool): selected messages to be shown as stated above.

        Returns:
            None
        """

        if need_download:
            self._heading_lbl.set_label(_('Waiting for Network…'))
            self._status_lbl.set_label(
                _("For a complete experience, a download of 15 KB is required. However, if you are not connected to the Internet or don't want to wait, you can skip this step and continue offline without some features."))
            self._offline_btn.set_visible(True)
            self._retry_check_btn.set_visible(True)
        else:
            self._heading_lbl.set_label(_('Getting things ready…'))
            self._status_lbl.set_label(_('Downloading data'))
            self._offline_btn.set_visible(False)
            self._retry_check_btn.set_visible(False)

    def _on_first_reach_done(self, source: GObject.Object | None, result: Gio.AsyncResult, data: object | None) -> None:
        """
        Callback for asynchronous network check, reached after the first call.
        If the network is available, proced with the download, otherwise keep checking every second until it becomes
        available or the user goes in offline mode.

        Args:
            source (GObject.Object or None): the object the asynchronous operation was started with.
            result (Gio.AsyncResult): a Gio.AsyncResult
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        try:
            network = Gio.NetworkMonitor.get_default().can_reach_finish(result)
        except GLib.Error:
            network = None

        if network:
            logging.info('[Setup] Network present, staring download')
            self._download_languages()
        else:
            self._has_network = False
            logging.error(
                '[Setup] Network not present, retrying in 10 seconds')
            # Continue checking in a separate thread
            GLib.Thread.new(None, self._loop_check_network)

    def _loop_check_network(self) -> None:
        """
        Function run in a separate thread to continously check for network connection every second until the operation
        is cancelled or the network is restored.
        If the network is restored, the download is completed and the thread killed.

        Args:
            None

        Returns:
            None
        """

        while not (self._cancellable.is_cancelled() or self._has_network):
            GLib.usleep(10000000)
            Gio.NetworkMonitor.get_default().can_reach_async(
                Gio.NetworkAddress.parse_uri('https://api.themoviedb.org', 80),
                self._cancellable,
                self._on_loop_reach_done,
                None
            )

        if self._has_network:
            logging.info('[Setup] Network present, staring download')
            self._download_languages()

        GLib.Thread.exit()

    def _on_loop_reach_done(self, source: GObject.Object | None, result: Gio.AsyncResult, user_data: object | None) -> None:
        """
        Callback for asynchronous network check, reached during the looped check.
        It sets the network presence flag based on the current condition.

        Args:
            source (GObject.Object or None): the object the asynchronous operation was started with.
            result (Gio.AsyncResult): a Gio.AsyncResult
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        try:
            self._has_network = Gio.NetworkMonitor.get_default().can_reach_finish(result)
        except GLib.Error:
            self._has_network = False
            logging.error(
                '[Setup] Network not present, retrying in 10 seconds')

    def _download_languages(self) -> None:
        """
        Completes the downlaod, stores the data in the db and sets the relevant GSettings.

        Args:
            None

        Results:
            None
        """

        self._update_ui(need_download=False)

        languages = tmdb.get_languages()
        for lang in languages:
            local.add_language(LanguageModel(lang))

        shared.schema.set_boolean('first-run', False)
        shared.schema.set_boolean('offline-mode', False)
        shared.schema.set_boolean('onboard-complete', True)
        logging.info('[Setup] First setup complete')
        self.emit('exit')

    @Gtk.Template.Callback('_on_offline_btn_clicked')
    def _on_offline_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for "clicked" signal.
        Stops the background network check and sets the app in offline mode. An option to retry on next launch is
        provided.

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        self._cancellable.cancel()

        shared.schema.set_boolean('offline-mode', True)
        logging.info('[Setup] Offline mode enabled')
        if not self._retry_check_btn.get_active():
            shared.schema.set_boolean('first-run', False)
            logging.info('[Setup] First setup partially complete')

        logging.info('[Setup] Setup not completed, retrying on next run')
        self.emit('exit')
