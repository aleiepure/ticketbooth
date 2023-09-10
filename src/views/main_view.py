# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later
from datetime import datetime, timedelta
from gettext import gettext as _
from gettext import pgettext as C_

from gi.repository import Adw, Gio, Gtk

from .. import shared  # type: ignore
from ..background_queue import (ActivityType, BackgroundActivity,
                                BackgroundQueue)
from ..models.movie_model import MovieModel
from ..models.series_model import SeriesModel
from ..providers.local_provider import LocalProvider as local
from ..providers.tmdb_provider import TMDBProvider as tmdb
from ..views.content_view import ContentView
from ..widgets.theme_switcher import ThemeSwitcher


@Gtk.Template(resource_path=shared.PREFIX + '/ui/views/main_view.ui')
class MainView(Adw.Bin):
    """
    This class rappresents the main view of the app.

    Properties:
        None

    Methods:
        refresh(): Causes the window to update its contents

    Signals:
        None
    """

    __gtype_name__ = 'MainView'

    _tab_stack = Gtk.Template.Child()
    _menu_btn = Gtk.Template.Child()
    _banner = Gtk.Template.Child()
    _background_indicator = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

        self._tab_stack.add_titled_with_icon(ContentView(movie_view=True),
                                             'movies',
                                             _('Movies'),
                                             'movies'
                                             )

        self._tab_stack.add_titled_with_icon(ContentView(movie_view=False),
                                             'series',
                                             _('TV Series'),
                                             'series'
                                             )

        shared.schema.bind('win-tab', self._tab_stack, 'visible-child-name', Gio.SettingsBindFlags.DEFAULT)
        shared.schema.bind('offline-mode', self._banner, 'revealed', Gio.SettingsBindFlags.GET)

        # Theme switcher (Adapted from https://gitlab.gnome.org/tijder/blueprintgtk/)
        self._menu_btn.get_popover().add_child(ThemeSwitcher(), 'themeswitcher')

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data: object | None) -> None:
        """
        Callback for "map" signal.
        Calls method to check if an automatic content update is due.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        if not shared.schema.get_boolean('first-run'):
            self._check_update_content()

    def _check_update_content(self) -> None:
        """
        Checks if a content update is due, triggering it by adding background activities, if necessary.

        Args:
            None

        Returns:
            None
        """

        last_check = datetime.fromisoformat(shared.schema.get_string('last-update'))

        match shared.schema.get_string('update-freq'):
            case 'day':
                if last_check + timedelta(days=1) < datetime.now():
                    BackgroundQueue.add(BackgroundActivity(ActivityType.UPDATE,
                                        C_('Background activity title', 'Automatic update'), self._update_content))
            case 'week':
                if last_check + timedelta(days=7) < datetime.now():
                    BackgroundQueue.add(BackgroundActivity(ActivityType.UPDATE,
                                        C_('Background activity title', 'Automatic update'), self._update_content))
            case 'month':
                if last_check + timedelta(days=30) < datetime.now():
                    BackgroundQueue.add(BackgroundActivity(ActivityType.UPDATE,
                                        C_('Background activity title', 'Automatic update'), self._update_content))
            case 'never':
                return

        shared.schema.set_string('last-update', datetime.now().strftime('%Y-%m-%d'))

    def _update_content(self, activity: BackgroundActivity) -> None:
        """
        Performs a content update on content added from TMDB.

        Args:
            activity (BackgroundActivity): the calling activity

        Returns:
            None
        """

        # Movies
        movies = local.get_all_movies()
        if movies:
            for movie in movies:    # type: ignore
                if not movie.manual:
                    new_movie = MovieModel(tmdb.get_movie(movie.id))
                    local.update_movie(old=movie, new=new_movie)

        # TV Series
        series = local.get_all_series()
        if series:
            for serie in series:    # type: ignore
                if not serie.manual:
                    local.delete_series(serie.id)
                    new_serie = SeriesModel(tmdb.get_serie(serie.id))
                    local.add_series(serie=new_serie)

        self.refresh()
        activity.end()

    def refresh(self) -> None:
        """
        Refreshes the visible window.

        Args:
            None

        Returns:
            None
        """
        self._tab_stack.get_child_by_name('movies').refresh_view()
        self._tab_stack.get_child_by_name('series').refresh_view()
