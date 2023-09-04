# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import glob
import os
from gettext import gettext as _
from gettext import pgettext as C_
from pathlib import Path

from gi.repository import Adw, Gio, GLib, GObject, Gtk

from . import shared  # type: ignore
from .models.language_model import LanguageModel
from .providers.local_provider import LocalProvider as local
from .providers.tmdb_provider import TMDBProvider as tmdb


@Gtk.Template(resource_path=shared.PREFIX + '/ui/preferences.ui')
class PreferencesWindow(Adw.PreferencesWindow):
    __gtype_name__ = 'PreferencesWindow'

    _download_group = Gtk.Template.Child()
    _language_comborow = Gtk.Template.Child()
    _language_model = Gtk.Template.Child()
    _update_freq_comborow = Gtk.Template.Child()
    _offline_group = Gtk.Template.Child()
    _offline_switch = Gtk.Template.Child()
    _tmdb_group = Gtk.Template.Child()
    _housekeeping_group = Gtk.Template.Child()
    _exit_cache_row = Gtk.Template.Child()
    _cache_row = Gtk.Template.Child()
    _data_row = Gtk.Template.Child()

    def __init__(self):
        super().__init__()
        self.language_change_handler = self._language_comborow.connect('notify::selected', self._on_language_changed)
        self._update_freq_comborow.connect('notify::selected', self._on_freq_changed)

        shared.schema.bind('onboard-complete', self._offline_group, 'sensitive', Gio.SettingsBindFlags.DEFAULT)
        shared.schema.bind('onboard-complete', self._download_group, 'visible', Gio.SettingsBindFlags.INVERT_BOOLEAN)
        # shared.schema.bind('onboard-complete', self._language_comborow, 'visible', Gio.SettingsBindFlags.DEFAULT)
        shared.schema.bind('onboard-complete', self._tmdb_group, 'sensitive', Gio.SettingsBindFlags.DEFAULT)

        shared.schema.bind('offline-mode', self._offline_switch, 'active', Gio.SettingsBindFlags.DEFAULT)
        shared.schema.bind('exit-remove-cache', self._exit_cache_row, 'active', Gio.SettingsBindFlags.DEFAULT)

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data: object | None) -> None:
        """
        Callback for the "map" signal.
        Populates dropdowns and checks if an automatic update of the content is due.

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        if shared.schema.get_boolean('onboard-complete'):
            self._setup_languages()

        # Update frequency dropdown
        match shared.schema.get_string('update-freq'):
            case 'never':
                self._update_freq_comborow.set_selected(0)
            case 'day':
                self._update_freq_comborow.set_selected(1)
            case 'week':
                self._update_freq_comborow.set_selected(2)
            case 'month':
                self._update_freq_comborow.set_selected(3)

        # Update check
        self._update_occupied_space()

    def _setup_languages(self):
        self._language_comborow.handler_block(self.language_change_handler)

        languages = local.get_all_languages()
        languages.pop(len(languages)-6)    # remove 'no language'
        for language in languages:
            self._language_model.append(language.name)

        self._language_comborow.set_selected(self._get_selected_language_index(shared.schema.get_string('tmdb-lang')))
        self._language_comborow.handler_unblock(self.language_change_handler)

    def _on_language_changed(self, pspec: GObject.ParamSpec, user_data: object | None) -> None:
        """
        Callback for "notify::selected" signal.
        Updates the prefered TMDB language in GSettings.

        Args:
            pspec (GObject.ParamSpec): The GParamSpec of the property which changed
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        language = self._get_selected_language(self._language_comborow.get_selected_item().get_string())
        shared.schema.set_string('tmdb-lang', language)

    def _on_freq_changed(self, pspec, user_data: object | None) -> None:
        """
        Callback for "notify::selected" signal.
        Updates the frequency for content updates in GSettings.

        Args:
            pspec (GObject.ParamSpec): The GParamSpec of the property which changed
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        freq = self._update_freq_comborow.get_selected()
        match freq:
            case 0:
                shared.schema.set_string('update-freq', 'never')
            case 1:
                shared.schema.set_string('update-freq', 'day')
            case 2:
                shared.schema.set_string('update-freq', 'week')
            case 3:
                shared.schema.set_string('update-freq', 'month')

    def _get_selected_language_index(self, iso_name: str) -> int:
        """
        Loops all available languages and returns the index of the one with the specified iso name. If a result is not found, it returns the index for English (37).

        Args:
            iso_name: a language's iso name

        Return:
            int with the index
        """

        for idx, language in enumerate(local.get_all_languages()):
            if language.iso_name == iso_name:
                return idx
        return 37

    def _get_selected_language(self, name: str) -> str:
        """
        Loops all available languages and returns the iso name of the one with the specified name. If a result is not found, it returns the iso name for English (en).

        Args:
            name: a language's name

        Return:
            str with the iso name
        """

        for language in local.get_all_languages():
            if language.name == name:
                return language.iso_name
        return 'en'

    @Gtk.Template.Callback('_on_download_activate')
    def _on_download_activate(self, user_data: object | None) -> None:
        """
        Completes the downlaod, stores the data in the db and sets the relevant GSettings.

        Args:
            None

        Results:
            None
        """

        Gio.NetworkMonitor.get_default().can_reach_async(
            Gio.NetworkAddress.parse_uri('https://api.themoviedb.org', 80),
            None,
            self._on_reach_done,
            None
        )

    def _on_reach_done(self, source: GObject.Object | None, result: Gio.AsyncResult, data: object | None) -> None:
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
            languages = tmdb.get_languages()
            for lang in languages:
                local.add_language(LanguageModel(lang))

            shared.schema.set_boolean('first-run', False)
            shared.schema.set_boolean('offline-mode', False)
            shared.schema.set_boolean('onboard-complete', True)

            self._setup_languages()
            Gio.NetworkMonitor.get_default().connect('network-changed', self._on_network_changed)
        else:
            dialog = Adw.MessageDialog.new(self,
                                           C_('message dialog heading', 'No Network'),
                                           C_('message dialog body', 'Connect to the Internet to complete the setup.'))
            dialog.add_response('ok', C_('message dialog action', 'OK'))
            dialog.present()

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

        shared.schema.set_boolean('offline-mode', GLib.Variant.new_boolean(not network_available))

    @Gtk.Template.Callback('_on_clear_cache_activate')
    def _on_clear_cache_activate(self, user_data: object | None) -> None:
        """
        Callback for "activated" signal.
        Shows a confirmation dialog to the user.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        builder = Gtk.Builder.new_from_resource(shared.PREFIX + '/ui/dialogs/message_dialogs.ui')
        _clear_cache_dialog = builder.get_object('_clear_cache_dialog')
        _clear_cache_dialog.set_transient_for(self)
        _clear_cache_dialog.choose(None, self._on_cache_message_dialog_choose, None)

    def _on_cache_message_dialog_choose(self,
                                        source: GObject.Object | None,
                                        result: Gio.AsyncResult,
                                        user_data: object | None) -> None:
        """
        Callback for the message dialog.
        Finishes the async operation and retrieves the user response. If the later is positive, deletes the stored cached data.

        Args:
            source (Gtk.Widget): object that started the async operation
            result (Gio.AsyncResult): a Gio.AsyncResult
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        result = Adw.MessageDialog.choose_finish(source, result)
        if result == 'cache_cancel':
            return

        files = glob.glob('*.jpg', root_dir=shared.cache_dir)
        for file in files:
            os.remove(shared.cache_dir / file)

        self._update_occupied_space()

    @Gtk.Template.Callback('_on_clear_activate')
    def _on_clear_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for "activated" signal.
        Shows a confirmation dialog to the user.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        builder = Gtk.Builder.new_from_resource(shared.PREFIX + '/ui/dialogs/message_dialogs.ui')
        _clear_data_dialog = builder.get_object('_clear_data_dialog')
        _movies_row = builder.get_object('_movies_row')
        _series_row = builder.get_object('_series_row')
        self._movies_checkbtn = builder.get_object('_movies_checkbtn')
        self._series_checkbtn = builder.get_object('_series_checkbtn')

        # TRANSLATORS: {number} is the number of titles
        _movies_row.set_subtitle(_('{number} Titles').format(number=len(local.get_all_movies())))
        _series_row.set_subtitle(_('{number} Titles').format(number=len(local.get_all_series())))

        _clear_data_dialog.set_transient_for(self)
        _clear_data_dialog.choose(None, self._on_data_message_dialog_choose, None)

    def _on_data_message_dialog_choose(self,
                                       source: GObject.Object | None,
                                       result: Gio.AsyncResult,
                                       user_data: object | None) -> None:
        """
        Callback for the message dialog.
        Finishes the async operation and retrieves the user response. If the later is positive, deletes the selected data.

        Args:
            source (Gtk.Widget): object that started the async operation
            result (Gio.AsyncResult): a Gio.AsyncResult
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        result = Adw.MessageDialog.choose_finish(source, result)
        if result == 'data_cancel':
            return

        # Movies
        if self._movies_checkbtn.get_active():
            for movie in local.get_all_movies():    # type: ignore
                local.delete_movie(movie.id)

        # TV Series
        if self._series_checkbtn.get_active():
            for serie in local.get_all_series():    # type: ignore
                local.delete_series(serie.id)

        self._update_occupied_space()
        self.get_transient_for().activate_action('win.refresh', None)

    def _calculate_space(self, directory: Path) -> float:
        """
        Given a directory, calculates the total space occupied on disk.

        Args:
            directory (Path): the directory to measure

        Returns:
            float with space occupied in MegaBytes (MB)
        """

        return sum(file.stat().st_size for file in directory.rglob('*'))/1024.0/1024.0

    def _update_occupied_space(self) -> None:
        """
        After calculating space occupied by cache and data, updates the ui labels to reflect the values.

        Args:
            None

        Returns:
            None
        """

        cache_space = self._calculate_space(shared.cache_dir)
        data_space = self._calculate_space(shared.data_dir)

        self._housekeeping_group.set_description(  # TRANSLATORS: {total_space:.2f} is the total occupied space
            _('Ticket Booth is currently using {total_space:.2f} MB. Use the options below to free some space.').format(total_space=cache_space+data_space))

        # TRANSLATORS: {space:.2f} is the occupied space
        self._cache_row.set_subtitle(_('{space:.2f} MB occupied').format(space=cache_space))
        self._data_row.set_subtitle(_('{space:.2f} MB occupied').format(space=data_space))
