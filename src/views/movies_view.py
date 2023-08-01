# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gio, GLib, GObject, Gtk

from .. import shared  # type: ignore
from ..models.movie_model import MovieModel
from ..providers.local_provider import LocalProvider as local
from ..views.details_view import DetailsView
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
        self._set_sorting_function()

        shared.schema.connect('changed::view-sorting', self._on_sort_changed)

    def _on_sort_changed(self, pspec: GObject.ParamSpec, user_data: object | None) -> None:
        """
        Callback for the "changed" signal.
        Calls the function to set the sorting function on the FlowBox.

        Args:
            pspec (GObject.ParamSpec): pspec of the changed property
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        self._set_sorting_function()

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
            btn = PosterButton(movie=movie)
            btn.connect('clicked', self._on_movie_clicked)
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

    def _on_movie_clicked(self, source: Gtk.Widget, movie: MovieModel) -> None:
        """
        Callback for the "clicked" signal.
        Opens the details view for the selected content.

        Args:
            source (Gtk.Widget): widget that emited the signal
            movie (MovieModel): associated movie

        Returns:
            None
        """

        win = DetailsView(movie)  # TODO: make it a navigationView when keybindings are available
        win.connect('deleted', lambda *args: self.refresh_view())
        win.present()

    def _set_sorting_function(self) -> None:
        """
        Based on the current setting, sets the sorting function of the FlowBox.

        Args:
            None

        Returns;
            None
        """

        match shared.schema.get_string('view-sorting'):
            case 'az':
                self._flow_box.set_sort_func(lambda child1, child2, user_data: (
                    (child1.get_child().title > child2.get_child().title) -
                    (child1.get_child().title < child2.get_child().title)
                ), None)
            case 'za':
                self._flow_box.set_sort_func(lambda child1, child2, user_data: (
                    (child1.get_child().title < child2.get_child().title) -
                    (child1.get_child().title > child2.get_child().title)
                ), None)
            case 'added-date-new':
                self._flow_box.set_sort_func(lambda child1, child2, user_data: (
                    (child1.get_child().movie.add_date < child2.get_child().movie.add_date) -
                    (child1.get_child().movie.add_date > child2.get_child().movie.add_date)
                ), None)
            case 'added-date-old':
                self._flow_box.set_sort_func(lambda child1, child2, user_data: (
                    (child1.get_child().movie.add_date > child2.get_child().movie.add_date) -
                    (child1.get_child().movie.add_date < child2.get_child().movie.add_date)
                ), None)
            case 'released-date-new':
                self._flow_box.set_sort_func(lambda child1, child2, user_data: (
                    (child1.get_child().movie.release_date < child2.get_child().movie.release_date) -
                    (child1.get_child().movie.release_date > child2.get_child().movie.release_date)
                ), None)
            case 'released-date-old':
                self._flow_box.set_sort_func(lambda child1, child2, user_data: (
                    (child1.get_child().movie.release_date > child2.get_child().movie.release_date) -
                    (child1.get_child().movie.release_date < child2.get_child().movie.release_date)
                ), None)
        self._flow_box.invalidate_sort()
