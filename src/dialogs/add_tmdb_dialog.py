# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gio, GLib, GObject, Gtk

from .. import shared  # type: ignore
from ..models.search_result_model import SearchResultModel
from ..providers.tmdb_provider import TMDBProvider


@Gtk.Template(resource_path=shared.PREFIX + '/ui/dialogs/add_tmdb.ui')
class AddTMDBDialog(Adw.Window):
    __gtype_name__ = 'AddTMDBDialog'

    _search_entry = Gtk.Template.Child()
    _stack = Gtk.Template.Child()
    _model = Gtk.Template.Child()

    def __init__(self, parent: Gtk.Window):
        super().__init__()
        self.set_transient_for(parent)

    @Gtk.Template.Callback('_on_searchentry_search_changed')
    def _on_searchentry_search_changed(self, user_data: GObject.GPointer):

        if self._model.get_property('n-items') > 0:
            self._model.remove_all()

        if self._search_entry.get_text():
            response = TMDBProvider().search(query=self._search_entry.get_text())

            if response['results']:

                # Populate model
                for result in response['results']:
                    if result['media_type'] in ['movie', 'tv']:
                        self._model.append(SearchResultModel(result))

                # Show results
                self._stack.set_visible_child_name('results')
            else:
                self._stack.set_visible_child_name('no-results')
        else:
            self._stack.set_visible_child_name('empty')
