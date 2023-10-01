# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from gi.repository import Adw, Gio, GLib, GObject, Gtk

from .. import shared  # type: ignore
from ..models.search_result_model import SearchResultModel
from ..providers.tmdb_provider import TMDBProvider


@Gtk.Template(resource_path=shared.PREFIX + '/ui/dialogs/add_tmdb.ui')
class AddTMDBDialog(Adw.Window):
    """
    This class represents the window used to search for movies and tv-series on TMDB.

    Properties:
        None

    Methods:
        None

    Signals:
        None
    """

    __gtype_name__ = 'AddTMDBDialog'

    _search_entry = Gtk.Template.Child()
    _stack = Gtk.Template.Child()
    _model = Gtk.Template.Child()

    def __init__(self, parent: Gtk.Window):
        super().__init__()
        self.set_transient_for(parent)

    @Gtk.Template.Callback('_on_searchentry_search_changed')
    def _on_searchentry_search_changed(self, user_data: object | None) -> None:
        """
        Callback for the "seach-changed" signal.
        Updates the GtkListModel used by the factory to populate the GtkListView.

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        logging.info(f'Search query: "{self._search_entry.get_text()}"')

        if self._model.get_property('n-items') > 0:
            self._model.remove_all()

        if not self._search_entry.get_text():
            self._stack.set_visible_child_name('empty')
            return

        response = TMDBProvider().search(query=self._search_entry.get_text())
        if not response['results']:
            self._stack.set_visible_child_name('no-results')
            logging.info('No results for query')
            return

        for result in response['results']:
            if result['media_type'] in ['movie', 'tv']:
                search_result = SearchResultModel(result)
                logging.info(
                    f'Found [{"movie" if search_result.media_type == "movie" else "TV series"}] {search_result.title}, {search_result.year}')
                self._model.append(search_result)

        self._stack.set_visible_child_name('results')
