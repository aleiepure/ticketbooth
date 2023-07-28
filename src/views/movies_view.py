# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gio, GLib, GObject, Gtk

from .. import shared  # type: ignore
from ..providers.local_provider import LocalProvider as local
from ..widgets.poster_button import PosterButton


@Gtk.Template(resource_path=shared.PREFIX + '/ui/views/movies_view.ui')
class MoviesView(Adw.Bin):
    """
    This class rappresents the movies view of the app.

    Properties:
        None

    Methods:
        refresh(): Causes the view to update its contents

    Signals:
        None
    """

    __gtype_name__ = 'MoviesView'

    _stack = Gtk.Template.Child()
    _flow_box = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

        self._stack.set_visible_child_name('loading')
        GLib.Thread.new(None, self._load_movies, None)

    def _load_movies(self, data: object | None) -> None:
        """
        For each movie currently in the db, creates a PosterButton and adds it to the FlowBox.

        Args:
            data (object or None): data passed to the thread

        Returns:
            None
        """

        movies = local.get_all_movies()

        if not movies:
            self._stack.set_visible_child_name('empty')
            return

        for movie in movies:
            btn = PosterButton(title=movie.title,
                               year=movie.release_date[0:4], tmdb_id=movie.id, poster_path=movie.poster_path)
            self._flow_box.insert(btn, -1)
        self._stack.set_visible_child_name('filled')

    def refresh_view(self) -> None:
        """
        Causes the view to refresh its contents by replacing the content of the FlowBox.

        Args:
            None

        Returns:
            None
        """

        self._stack.set_visible_child_name('loading')

        while self._flow_box.get_child_at_index(0):
            self._flow_box.remove(self._flow_box.get_child_at_index(0))

        GLib.Thread.new(None, self._load_movies, None)
