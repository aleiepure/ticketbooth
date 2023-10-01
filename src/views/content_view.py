# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from gi.repository import Adw, GLib, GObject, Gtk

import src.providers.local_provider as local

from .. import shared  # type: ignore
from ..models.movie_model import MovieModel
from ..models.series_model import SeriesModel
from ..pages.details_page import DetailsView
from ..widgets.poster_button import PosterButton


@Gtk.Template(resource_path=shared.PREFIX + '/ui/views/content_view.ui')
class ContentView(Adw.Bin):
    """
    This class represents the content grid view.

    Properties:
        None

    Methods:
        refresh(): Causes the view to update its contents

    Signals:
        None
    """

    __gtype_name__ = 'ContentView'

    movie_view = GObject.Property(type=bool, default=True)
    icon_name = GObject.Property(type=str, default='movies')

    _stack = Gtk.Template.Child()
    _updating_status_lbl = Gtk.Template.Child()
    _flow_box = Gtk.Template.Child()

    def __init__(self, movie_view: bool):
        super().__init__()
        self.movie_view = movie_view
        self.icon_name = 'movies' if self.movie_view else 'series'

        self._stack.set_visible_child_name('loading')

        self._load_content(self.movie_view)

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

    def _load_content(self, movie_view: bool) -> None:
        """
        For each title currently in the db, creates a PosterButton and adds it to the FlowBox.

        Args:
            movie_view (bool): if true it will load movies, otherwise it will load series

        Returns:
            None
        """

        # self._stack.set_visible_child_name('loading')
        if movie_view:
            content = local.LocalProvider.get_all_movies()
        else:
            content = local.LocalProvider.get_all_series()

        if not content:
            self._stack.set_visible_child_name('empty')
            return
        else:
            self._stack.set_visible_child_name('filled')

        for item in content:
            logging.debug(
                f'Created poster button for [{"movie" if self.movie_view else "TV series"}] {item.title}')
            btn = PosterButton(content=item)
            btn.connect('clicked', self._on_clicked)
            self._flow_box.insert(btn, -1)

        idx = 0
        while self._flow_box.get_child_at_index(idx):
            self._flow_box.get_child_at_index(idx).set_focusable(False)
            idx += 1

        # self._stack.set_visible_child_name('filled')

    def refresh_view(self) -> None:
        """
        Causes the view to refresh its contents by replacing the content of the FlowBox.

        Args:
            None

        Returns:
            None
        """

        # self._stack.set_visible_child_name('loading')

        self._flow_box.remove_all()

        self._load_content(self.movie_view)

    def _on_clicked(self, source: Gtk.Widget, content: MovieModel | SeriesModel) -> None:
        """
        Callback for the "clicked" signal.
        Opens the details view for the selected content.

        Args:
            source (Gtk.Widget): widget that emited the signal
            movie (MovieModel): associated movie

        Returns:
            None
        """

        logging.info(
            f'Clicked on [{"movie" if self.movie_view else "TV series"}] {content.title}')
        page = DetailsView(content)
        page.connect('deleted', lambda *args: self.refresh_view())
        self.get_ancestor(Adw.NavigationView).push(page)

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
                    (child1.get_child().content.add_date < child2.get_child().content.add_date) -
                    (child1.get_child().content.add_date >
                     child2.get_child().content.add_date)
                ), None)
            case 'added-date-old':
                self._flow_box.set_sort_func(lambda child1, child2, user_data: (
                    (child1.get_child().content.add_date > child2.get_child().content.add_date) -
                    (child1.get_child().content.add_date <
                     child2.get_child().content.add_date)
                ), None)
            case 'released-date-new':
                self._flow_box.set_sort_func(lambda child1, child2, user_data: (
                    (child1.get_child().content.release_date < child2.get_child().content.release_date) -
                    (child1.get_child().content.release_date >
                     child2.get_child().content.release_date)
                ), None)
            case 'released-date-old':
                self._flow_box.set_sort_func(lambda child1, child2, user_data: (
                    (child1.get_child().content.release_date > child2.get_child().content.release_date) -
                    (child1.get_child().content.release_date <
                     child2.get_child().content.release_date)
                ), None)
        self._flow_box.invalidate_sort()
