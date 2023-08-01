# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import glob
from typing import Callable

import requests
from gi.repository import Gio, GLib, GObject, Gtk

from .. import shared  # type: ignore
from ..models.movie_model import MovieModel


@Gtk.Template(resource_path=shared.PREFIX + '/ui/widgets/poster_button.ui')
class PosterButton(Gtk.Box):
    """
    Widget shown in the main view with poster, title, and release year.

    Properties:
        title (str): content's title
        year (str): content's release year
        tmdb_id (int): content's tmdb id
        poster_path (str): content's poster uri

    Methods:
        None

    Signals:
        clicked(movie: MovieModel): emited when the user clicks on the widget
    """

    __gtype_name__ = 'PosterButton'

    _picture = Gtk.Template.Child()
    _spinner = Gtk.Template.Child()
    _year_lbl = Gtk.Template.Child()

    # Properties
    title = GObject.Property(type=str, default='')
    year = GObject.Property(type=str, default='')
    tmdb_id = GObject.Property(type=int, default=0)
    poster_path = GObject.Property(type=str, default='')
    movie = GObject.Property(type=MovieModel, default=None)

    __gsignals__ = {
        'clicked': (GObject.SIGNAL_RUN_FIRST, None, (MovieModel,)),
    }

    def __init__(self, movie: MovieModel):
        super().__init__()
        self.title = movie.title
        self.year = movie.release_date[0:4]
        self.tmdb_id = movie.id
        self.poster_path = movie.poster_path
        self.movie = movie

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

    @Gtk.Template.Callback('_on_poster_btn_clicked')
    def _on_poster_btn_clicked(self, user_data: object | None) -> None:
        self.emit('clicked', self.movie)
