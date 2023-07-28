# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import glob
from typing import Callable

import requests
from gi.repository import Gio, GLib, GObject, Gtk

from .. import shared  # type: ignore


@Gtk.Template(resource_path=shared.PREFIX + '/ui/widgets/poster_button.ui')
class PosterButton(Gtk.Box):
    """
    Widget shown in the main view with poster, title, and release year.

    Properties:
        title (str): content's title
        year (str): content's release year
        tmdb_id (int): content's tmdb id
        poster_path (str): content's poster uri
    """

    __gtype_name__ = 'PosterButton'

    _picture = Gtk.Template.Child()
    _spinner = Gtk.Template.Child()
    _year_lbl = Gtk.Template.Child()

    # Properties
    title = GObject.Property(type=str, default='')
    year = GObject.Property(type=str)
    tmdb_id = GObject.Property(type=int, default=0)
    poster_path = GObject.Property(type=str, default='')

    def __init__(self, title: str = '', year: str = '', tmdb_id: int = 0, poster_path: str = ''):
        super().__init__()
        self.title = title
        self.year = year
        self.tmdb_id = tmdb_id
        self.poster_path = poster_path

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data: object | None) -> None:
        """
        Callback for the 'map' signal.
        Sets images and hides release year label if not present.

        Args:
            user_data (object or None): data passed to the callback

        Returns:
            None
        """

        self._picture.set_file(Gio.File.new_for_uri(self.poster_path))
        self._spinner.set_visible(False)
        if not self.year:
            self._year_lbl.set_visible(False)
