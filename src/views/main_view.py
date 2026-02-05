# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from datetime import datetime, timedelta
from gettext import gettext as _
from gettext import pgettext as C_
from gettext import ngettext as N_

from gi.repository import Adw, Gio, GObject, Gtk

from .. import shared  # type: ignore
from ..background_queue import (ActivityType, BackgroundActivity,
                                BackgroundQueue)
from ..models.movie_model import MovieModel
from ..models.series_model import SeriesModel
from ..providers.local_provider import LocalProvider as local
from ..providers.tmdb_provider import TMDBProvider as tmdb
from ..views.content_grid_view import ContentGridView
from ..widgets.theme_switcher import ThemeSwitcher


@Gtk.Template(resource_path=shared.PREFIX + '/ui/views/main_view.ui')
class MainView(Adw.Bin):
    """
    This class represents the main view of the app.

    Properties:
        None

    Methods:
        refresh(): Causes the window to update its contents

    Signals:
        None
    """

    __gtype_name__ = 'MainView'

    _tab_stack = Gtk.Template.Child()
    _show_search_btn = Gtk.Template.Child()
    _menu_btn = Gtk.Template.Child()
    _banner = Gtk.Template.Child()
    _background_indicator = Gtk.Template.Child()
    _search_bar = Gtk.Template.Child()
    _search_mode = Gtk.Template.Child()
    _search_entry = Gtk.Template.Child()

    _needs_refresh = ''

    def __init__(self, window):
        super().__init__()
        self.app = window.app

        # Movies Tab (Navigation Controller)
        self.movies_nav = Adw.NavigationView()
        self.movies_dash = ContentGridView(movie_view=True, dashboard_mode=True)
        self.movies_dash.connect('show-all', self._on_show_all_movies)
        # Wrap in NavigationPage (required by Adw.NavigationView API)
        movies_page = Adw.NavigationPage(child=self.movies_dash, title=C_('Category', 'Movies'))
        self.movies_nav.push(movies_page)
        
        self._tab_stack.add_titled_with_icon(self.movies_nav,
                                             'movies',
                                             C_('Category', 'Movies'),
                                             'movies'
                                             )

        # Series Tab (Navigation Controller)
        self.series_nav = Adw.NavigationView()
        self.series_dash = ContentGridView(movie_view=False, dashboard_mode=True)
        self.series_dash.connect('show-all', self._on_show_all_series)
        # Wrap in NavigationPage (required by Adw.NavigationView API)
        series_page = Adw.NavigationPage(child=self.series_dash, title=C_('Category', 'TV Series'))
        self.series_nav.push(series_page)

        self._tab_stack.add_titled_with_icon(self.series_nav,
                                             'series',
                                             C_('Category', 'TV Series'),
                                             'series'
                                             )

        shared.schema.bind('win-tab', self._tab_stack,
                           'visible-child-name', Gio.SettingsBindFlags.DEFAULT)
        shared.schema.bind('offline-mode', self._banner,
                           'revealed', Gio.SettingsBindFlags.GET)
        shared.schema.bind('search-enabled', self._search_bar,
                           'search-mode-enabled', Gio.SettingsBindFlags.DEFAULT)
        shared.schema.bind('search-enabled', self._show_search_btn,
                           'active', Gio.SettingsBindFlags.DEFAULT)

        self._search_mode.connect(
            'notify::selected', self._on_search_mode_changed)

        self._tab_stack.connect(
            'notify::visible-child-name', self._check_needs_refresh)

        # Theme switcher (Adapted from https://gitlab.gnome.org/tijder/blueprintgtk/)
        self._menu_btn.get_popover().add_child(ThemeSwitcher(), 'themeswitcher')

    def _check_needs_refresh(self, pspec: GObject.ParamSpec, user_data: object | None) -> None:
        """
        Checks if the tab switched to is pending a refresh and does it if needed.

        Args:
            pspec (GObject.ParamSpec): pspec of the changed property
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """
        if self._tab_stack.get_visible_child_name() == 'movies' and self._needs_refresh == 'movies':
            self._refresh_nav_view(self.movies_nav)
            logging.info('Refreshed movies tab')
            self._needs_refresh = ''
        elif self._tab_stack.get_visible_child_name() == 'series' and self._needs_refresh == 'series':
            self._refresh_nav_view(self.series_nav)
            logging.info('Refreshed TV Series tab')
            self._needs_refresh = ''

    def _refresh_nav_view(self, nav_view: Adw.NavigationView) -> None:
        """Helper to refresh the currently visible page in a NavView."""
        page = nav_view.get_visible_page()
        if page:
            view = page.get_child()
            if hasattr(view, 'refresh_view'):
                view.refresh_view()

    def _on_show_all_movies(self, view, data=None):
        """Transition to Full Movie List."""
        full_view = ContentGridView(movie_view=True, dashboard_mode=False)
        # Wrap in NavigationPage for proper back button support
        full_page = Adw.NavigationPage(child=full_view, title=_("All Movies"))
        self.movies_nav.push(full_page)

    def _on_show_all_series(self, view, data=None):
        """Transition to Full Series List."""
        full_view = ContentGridView(movie_view=False, dashboard_mode=False)
        # Wrap in NavigationPage for proper back button support
        full_page = Adw.NavigationPage(child=full_view, title=_("All TV Series"))
        self.series_nav.push(full_page)

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

        last_check = datetime.fromisoformat(
            shared.schema.get_string('last-update'))
        frequency = shared.schema.get_string('update-freq')
        last_notification_check = datetime.fromisoformat(
            shared.schema.get_string('last-notification-update'))

        if last_notification_check + timedelta(hours=12) < datetime.now():
            shared.schema.set_string(
                'last-notification-update', datetime.now().strftime('%Y-%m-%d %H:%M'))
            logging.info('Starting automatic notification list update...')
            BackgroundQueue.add(
                activity=BackgroundActivity(
                    activity_type=ActivityType.UPDATE,
                    title=C_('Notification List activity title',
                             'Automatic update of notification list'),
                    task_function=self._update_notification_list),
                on_done=self._on_notification_list_done)

        logging.debug(
            f'Last update done on {last_check}, frequency {frequency}')

        run = True
        match frequency:
            case 'day':
                if last_check + timedelta(days=1) < datetime.now():
                    logging.info('Starting automatic update...')
                    BackgroundQueue.add(
                        activity=BackgroundActivity(
                            activity_type=ActivityType.UPDATE,
                            title=C_('Background activity title',
                                     'Automatic update'),
                            task_function=self._update_content),
                        on_done=self._on_update_done)
            case 'week':
                if last_check + timedelta(days=7) < datetime.now():
                    logging.info('Starting automatic update...')
                    BackgroundQueue.add(
                        activity=BackgroundActivity(
                            activity_type=ActivityType.UPDATE,
                            title=C_('Background activity title',
                                     'Automatic update'),
                            task_function=self._update_content),
                        on_done=self._on_update_done)
            case 'month':
                if last_check + timedelta(days=30) < datetime.now():
                    logging.info('Starting automatic update...')
                    BackgroundQueue.add(
                        activity=BackgroundActivity(
                            activity_type=ActivityType.UPDATE,
                            title=C_('Background activity title',
                                     'Automatic update'),
                            task_function=self._update_content),
                        on_done=self._on_update_done)
            case 'never':
                return

        shared.schema.set_string(
            'last-update', datetime.now().strftime('%Y-%m-%d'))

    def _update_content(self, activity: BackgroundActivity) -> None:
        """
        Performs a content update on content added from TMDB.

        Args:
            activity (BackgroundActivity): the calling activity

        Returns:
            None
        """

        movies = local.get_all_movies()
        if movies:
            for movie in movies:    # type: ignore
                if not movie.manual:
                    new_movie = MovieModel(tmdb.get_movie(movie.id))
                    local.update_movie(old=movie, new=new_movie)

        series = local.get_all_series()
        if series:
            for serie in series:    # type: ignore
                if not serie.manual:
                    new_serie = SeriesModel(tmdb.get_serie(serie.id))
                    local.update_series(old=serie, new=new_serie)

    def _on_update_done(self,
                        source: GObject.Object,
                        result: Gio.AsyncResult,
                        cancellable: Gio.Cancellable,
                        activity: BackgroundActivity):
        """Callback to complete async activity"""

        self.refresh()
        logging.info('Automatic update done')
        activity.end()

    def _update_notification_list(self, activity: BackgroundActivity) -> None:
        """
        Performs a content update on the notification list.

        Args:
            activity (BackgroundActivity): the calling activity

        Returns:
            None
        """
        series = local.get_all_series_notification_list()

        new_release_series = []
        soon_release_series = []
        out_of_production_series = []

        for serie in series:

            # =============================================================================
            # FIX: serie.last_air_date can be None
            # =============================================================================
            # TMDB sometimes returns null for last_air_date (unreleased series etc.)
            # In this case strptime() will crash: TypeError
            # Solution: For series without dates, just update data, skip comparison
            # =============================================================================
            if not serie.last_air_date or not serie.last_air_date.strip():
                # Get new data from TMDB
                new_serie = SeriesModel(tmdb.get_serie(serie.id))
                
                # Production end check (doesn't require date)
                if serie.in_production == 1 and new_serie.in_production == 0:
                    local.set_recent_change_status(serie.id, True)
                    out_of_production_series.append(new_serie)
                    local.set_notification_list_status(serie.id, False)
                
                # Update data
                serie = local.get_series_by_id(serie.id)
                local.update_series(serie, new_serie)
                continue

            last_air_date = datetime.strptime(serie.last_air_date, '%Y-%m-%d')

            # Get the latest info for the series from TMDB
            new_serie = SeriesModel(tmdb.get_serie(serie.id))
            
            # =============================================================================
            # FIX: new_serie.last_air_date can also be None
            # =============================================================================
            # Series newly fetched from TMDB API can also have null last_air_date
            # Evidence: TMDB API documentation + SeriesModel line 174 has no check
            # =============================================================================
            if not new_serie.last_air_date or not new_serie.last_air_date.strip():
                # Production end check (doesn't require date)
                if serie.in_production == 1 and new_serie.in_production == 0:
                    local.set_recent_change_status(serie.id, True)
                    out_of_production_series.append(new_serie)
                    local.set_notification_list_status(serie.id, False)
                # Update data
                serie = local.get_series_by_id(serie.id)
                local.update_series(serie, new_serie)
                continue
            
            new_last_air_date = datetime.strptime(
                new_serie.last_air_date, '%Y-%m-%d')
            if new_serie.next_air_date != '':
                new_next_air_date = datetime.strptime(
                    new_serie.next_air_date, '%Y-%m-%d')
            else:
                # create bogus next air date if it does not exist
                new_next_air_date = datetime.now() + timedelta(days=10)

            # Check if the latest release is newer than the last saved in the database -> new release has come out.
            if last_air_date < new_last_air_date:
                # Set the new release status and add the series to the new releases list and set soon_release to false
                local.set_new_release_status(serie.id, True)
                local.set_soon_release_status(serie.id, False)
                local.set_recent_change_status(serie.id, True)
                new_release_series.append(new_serie)
                # we only save one, since we do not use it if more than one series has a new release
                new_release_series_span = datetime.now() - new_last_air_date

            # Check if the next air date is set to soon (7 days in the future)
            if datetime.now() + timedelta(days=shared.SOON_RELEASE_THRESHOLD_SERIES) > new_next_air_date:
                local.set_soon_release_status(serie.id, True)
                # if we also detect a considerable amount of time bewteen epsidoe notify user that the series has new releases coming soon.
                # 3 weeks are chosen to include the new streaming release model of two chunks a month apart but not spam the user for weekly or bi-weekly releases
                if new_next_air_date - timedelta(days=20) > last_air_date:
                    local.set_recent_change_status(serie.id, True)
                    soon_release_series.append(new_serie)
                    soon_release_series_span = new_next_air_date - datetime.now()

            # Check if the series went from in production to not in production
            if serie.in_production == 1 and new_serie.in_production == 0:
                local.set_recent_change_status(serie.id, True)
                out_of_production_series.append(new_serie)
                local.set_notification_list_status(serie.id, False)

            # refetch serie to get all the correct flags that we set from the database
            serie = local.get_series_by_id(serie.id)
            local.update_series(serie, new_serie)

        movies = local.get_all_movies_notification_list()

        new_release_movies = []
        soon_release_movies = []

        for movie in movies:

            # Get the latest info for the movie from TMDB
            new_movie = MovieModel(tmdb.get_movie(movie.id))
            release_date = datetime.strptime(
                new_movie.release_date, '%Y-%m-%d')

            if release_date < datetime.now():
                local.set_recent_change_status(movie.id, True, movie=True)
                local.set_new_release_status(movie.id, True, movie=True)
                local.set_soon_release_status(movie.id, False, movie=True)
                if not movie.new_release:  # if new_release was not set send a notification
                    new_release_movies_span = datetime.now() - release_date
                    new_release_movies.append(new_movie)
            elif release_date < datetime.now() + timedelta(days=shared.SOON_RELEASE_THRESHOLD_MOVIE):
                local.set_recent_change_status(movie.id, True, movie=True)
                local.set_soon_release_status(movie.id, True, movie=True)
                if not movie.soon_release:  # if soon_release was not set send a notification
                    soon_release_movies_span = release_date - datetime.now()
                    soon_release_movies.append(new_movie)
            # For movies we do not need to refetch the movie from the local db since the new data gets inserted by SQL UPDATE
            local.update_movie(movie, new_movie)

        def length_check(x): return len(x) > 0
        count = length_check(new_release_movies) + length_check(new_release_series) + length_check(
            soon_release_movies) + length_check(soon_release_series) + length_check(out_of_production_series)

        if count == 0:
            return
        elif count == 1:
            if new_release_series:
                if len(new_release_series) == 1:
                    # TRANSLATOR: {title} is the title of the series
                    title = _("New release for {title}").format(
                        title=new_release_series[0].title)
                    # TRANSLATOR: {title} is the title of the series and {days} the number of days
                    body = N_("A new episode of {title} was released {days} day ago.", "A new episode of {title} was released {days} days ago.",
                              new_release_series_span.days).format(title=new_release_series[0].title, days=new_release_series_span.days)
                else:
                    # TRANSLATOR: {num} is the number of TV Series
                    title = _("New release for {num} TV series on your watchlist").format(
                        num=len(new_release_series))
                    series = ", ".join(new.title for new in new_release_series)
                    # TRANSLATOR: {series} is a list of TV series seperated by a comma
                    body = _("The TV Series are {series}.").format(
                        series=series)

            if soon_release_series:
                if len(soon_release_series) == 1:
                    # TRANSLATOR: {title} is the title of the series with a new episode soon
                    title = _("{title} will have a release soon").format(
                        title=soon_release_series[0].title)
                    # TRANSLATOR: {title} is the title of the series and {days} the number of days
                    body = N_("A new episode will release in {days} day.", "A new episode will release in {days} days.", soon_release_series_span.days).format(
                        title=soon_release_series[0].title, days=soon_release_series_span.days)
                else:
                    # TRANSLATOR: {num} is the number of TV Series
                    title = _("{num} TV Series on your watchlist will have a new episode soon").format(
                        num=len(soon_release_series))
                    series = ", ".join(
                        soon.title for soon in soon_release_series)
                    # TRANSLATOR: {series} is a list of all series affected seperated by a comma
                    body = _("The TV Series are {series}.").format(
                        series=series)

            if out_of_production_series:
                if len(out_of_production_series) == 1:
                    # TRANSLATOR: {title} is the title of the series that has gone out of production
                    title = _("{title} has gone out of production").format(
                        title=out_of_production_series[0].title)
                    # TRANSLATOR: {title} is the title of the series that has gone out of production
                    body = _("{title} has wrapped up its run. Now is the perfect time to revisit your favorite moments or find the next binge!")
                else:
                    # TRANSLATOR: {num} is the number of TV Series
                    title = _("{num} TV Series of your watchlist have gone out of production").format(
                        num=len(out_of_production_series))
                    series = ", ".join(
                        out.title for out in out_of_production_series)
                    # TRANSLATOR: {series} is a list of all series affected seperated by a comma
                    body = _("The TV Series are {series}.").format(
                        series=series)

            if new_release_movies:
                if len(new_release_movies) == 1:
                    # TRANSLATOR: {title} is the title of the movie that has had its release
                    title = _("{title} has had its release!").format(
                        title=new_release_movies[0].title)
                    # TRANSLATOR: {title} is the title of the series and {days} the number of days
                    body = N_("{title} was released {days} day ago.", "{title} was released {days} days ago.", new_release_movies_span.days).format(
                        title=new_release_movies[0].title, days=new_release_movies_span.days)
                else:
                    title = _("{num} movies on your watchlist have had their releases.").format(
                        num=len(new_release_movies))
                    movies = ", ".join(new.title for new in new_release_movies)
                    # TRANSLATOR: {movies} is a list of all movies affected seperated by a comma
                    body = _("The movies are {movies}.").format(movies=movies)

            if soon_release_movies:
                if len(soon_release_movies) == 1:
                    # TRANSLATOR: {title} is the title of the movie that will have its release soon
                    title = _("{title} will have its release soon!").format(
                        title=soon_release_movies[0].title)
                    # TRANSLATOR: {title} is the title of the movie and {days} the number of days
                    body = N_("{title} will have its release in {days} day.", "{title} will have its release in {days} days.", soon_release_movies_span.days).format(
                        title=soon_release_movies[0].title, days=soon_release_movies_span.days)
                else:
                    # TRANSLATOR: {num} is the number of movies
                    title = _("{num} movies on your watchlist will have their releases soon")
                    movies = ", ".join(soon.title for soon in soon_release_movies)
                    # TRANSLATOR: {movies} will be list of all series affected seperated by a comma
                    body = _("The movies are {movies}.").format(movies=movies)

            notification = Gio.Notification.new(title)
            notification.set_body(body)
            self.app.send_notification(None, notification)
        else:
            count_movies = len(new_release_movies) + len(soon_release_movies)
            count_series = len(
                new_release_series) + len(soon_release_series) + len(out_of_production_series)
            # TRANSLATOR: {num} is the number of affected items
            title = _("{num} items of your watchlist have an update").format(
                num=count_movies + count_series)

            if count_movies > 0 and count_series > 0:
                # TRANSLATOR: {count_movies} is the number of movies
                movie = N_("These updates affect {count_movies} movie", "These updates affect {count_movies} movies", count_movies)
                # TRANSLATOR: the connector between the two parts of the sentence (foo and bar)
                connector = _(" and ")
                # TRANSLATOR: {count_series} is the number of series
                series = N_(" {count_series} TV serie", " {count_series} TV series", count_series)
                
                body = f"{movie}{connector}{series}."
            elif count_movies > 0:
                # TRANSLATOR: {count_movies} is the number of movies
                body = N_("These updates affect {count_movies} movie", "These updates affect {count_movies} movies", count_movies)
            elif count_series > 0:
                # TRANSLATOR: {count_series} is the number of series
                body = N_("These updates affect {count_series} TV serie", "These updates affect {count_series} TV series", count_series)

            notification = Gio.Notification.new(title)
            notification.set_body(body)
            self.app.send_notification(None, notification)

    def _on_notification_list_done(self,
                                   source: GObject.Object,
                                   result: Gio.AsyncResult,
                                   cancellable: Gio.Cancellable,
                                   activity: BackgroundActivity):
        """Callback to complete async activity"""

        self.refresh()
        logging.info('Automatic notification list update done')
        activity.end()

    def refresh(self, show_loading: bool = True) -> None:
        """
        Refreshes the visible window.

        Args:
            show_loading: If False, don't show loading overlay (for silent updates)

        Returns:
            None
        """

        if self._tab_stack.get_visible_child_name() == 'movies':
            self._refresh_nav_view(self.movies_nav)
            logging.info('Refreshed movies tab')
            self._needs_refresh = 'series'
        else:
            self._refresh_nav_view(self.series_nav)
            logging.info('Refreshed TV series tab')
            self._needs_refresh = 'movies'

    @Gtk.Template.Callback()
    def _on_searchentry_search_changed(self, user_data: GObject.GPointer | None) -> None:
        shared.schema.set_string('search-query', self._search_entry.get_text())

    @Gtk.Template.Callback()
    def _on_search_btn_toggled(self, user_data: GObject.GPointer | None) -> None:
        shared.schema.set_boolean(
            'search-enabled', self._show_search_btn.get_active())
        shared.schema.set_string('search-query', '')

    def _on_search_mode_changed(self, pspec: GObject.ParamSpec, user_data: object | None) -> None:
        if self._search_mode.get_selected() == 0:
            shared.schema.set_string('search-mode', 'title')
        elif self._search_mode.get_selected() == 1:
            shared.schema.set_string('search-mode', 'genre')
        elif self._search_mode.get_selected() == 2:
            shared.schema.set_string('search-mode', 'overview')
        elif self._search_mode.get_selected() == 3:
            shared.schema.set_string('search-mode', 'notes')
        elif self._search_mode.get_selected() == 4:
            shared.schema.set_string('search-mode', 'tmdb-id')
