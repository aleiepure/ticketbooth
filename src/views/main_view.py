# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from datetime import datetime, timedelta
from gettext import gettext as _
from gettext import pgettext as C_

from gi.repository import Adw, Gio, GObject, Gtk

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
    _menu_btn = Gtk.Template.Child()
    _banner = Gtk.Template.Child()
    _background_indicator = Gtk.Template.Child()

    _needs_refresh = ''

    def __init__(self, window):
        super().__init__()
        self.app = window.app
 

        self._tab_stack.add_titled_with_icon(ContentView(movie_view=True),
                                             'movies',
                                             C_('Category', 'Movies'),
                                             'movies'
                                             )

        self._tab_stack.add_titled_with_icon(ContentView(movie_view=False),
                                             'series',
                                             C_('Category', 'TV Series'),
                                             'series'
                                             )

        shared.schema.bind('win-tab', self._tab_stack,
                           'visible-child-name', Gio.SettingsBindFlags.DEFAULT)
        shared.schema.bind('offline-mode', self._banner,
                           'revealed', Gio.SettingsBindFlags.GET)

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
            self._tab_stack.get_child_by_name('movies').refresh_view()
            logging.info('Refreshed movies tab')
            self._needs_refresh = ''
        elif self._tab_stack.get_visible_child_name() == 'series' and self._needs_refresh == 'series':
            self._tab_stack.get_child_by_name('series').refresh_view()
            logging.info('Refreshed TV Series tab')
            self._needs_refresh = ''

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
                    local.update_series(old=serie,new=new_serie)

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
            
            last_air_date = datetime.strptime(serie.last_air_date, '%Y-%m-%d')

            # Get the latest info for the series from TMDB
            new_serie = SeriesModel(tmdb.get_serie(serie.id))
            new_last_air_date = datetime.strptime(new_serie.last_air_date, '%Y-%m-%d')
            if new_serie.next_air_date != '':
                new_next_air_date = datetime.strptime(new_serie.next_air_date, '%Y-%m-%d')
            else:
                new_next_air_date = datetime.now() + timedelta(days = 10) # create bogus next air date if it does not exist
                
            # Check if the latest release is newer than the last saved in the database -> new release has come out.
            if last_air_date < new_last_air_date:
                # Set the new release status and add the series to the new releases list and set soon_release to false
                local.set_new_release_status(serie.id, True)
                local.set_soon_release_status(serie.id, False)
                local.set_recent_change_status(serie.id, True)
                new_release_series.append(new_serie)
                new_release_series_span = datetime.now() - new_last_air_date  #we only save one, since we do not use it if more than one series has a new release
            
            # Check if the next air date is set to soon (7 days in the future)
            if datetime.now() + timedelta(days=7) > new_next_air_date:
                local.set_soon_release_status(serie.id, True)
                # if we also detect a considerable amount of time bewteen epsidoe notify user that the series has new releases coming soon.
                # 3 weeks are chosen to include the new streaming release model of two chunks a month apart but not spam the user for weekly or bi-weekly releases
                if new_next_air_date - timedelta(days=20) > last_air_date:
                    local.set_recent_change_status(serie.id, True)
                    soon_release_series.append(new_serie)
                    soon_release_series_span =  new_next_air_date - datetime.now()
            
            # Check if the series went from in production to not in production
            if serie.in_production == 1 and new_serie.in_production == 0:
                local.set_recent_change_status(serie.id, True)
                out_of_production.append(new_serie)
                local.set_notification_list_status(serie.id, False)

            serie = local.get_series_by_id(serie.id) #refetch serie to get all the correct flags that we set from the database
            local.update_series(serie, new_serie)

        movies = local.get_all_movies_notification_list()

        new_release_movies = []
        soon_release_movies = []

        for movie in movies:
            
            # Get the latest info for the movie from TMDB
            new_movie = MovieModel(tmdb.get_movie(movie.id))
            release_date = datetime.strptime(new_movie.release_date, '%Y-%m-%d')

            if release_date < datetime.now():
                local.set_recent_change_status(movie.id, True, movie=True)
                local.set_new_release_status(movie.id, True, movie=True)
                local.set_soon_release_status(movie.id, False, movie=True)
                if not movie.new_release: #if new_release was not set send a notification
                    new_release_movies_span = datetime.now() - release_date
                    new_release_movies.append(new_movie)
            elif release_date < datetime.now() + timedelta(days=14):
                local.set_recent_change_status(movie.id, True, movie=True)
                local.set_soon_release_status(movie.id, True, movie=True)
                if not movie.soon_release: #if soon_release was not set send a notification
                    soon_release_movies_span = release_date - datetime.now()
                    soon_release_movies.append(new_movie)
            #For movies we do not need to refetch the movie from the local db since the new data gets inserted by SQL UPDATE
            local.update_movie(movie, new_movie)

        length_check = lambda x: len(x) > 0
        count = length_check(new_release_movies) + length_check(new_release_series) + length_check(soon_release_movies) + length_check(soon_release_series) + length_check(out_of_production_series)

        if count == 0:
            return
        elif count == 1:
            if new_release_series:
                if len(new_release_series) == 1:
                    title = _("New release for " + new_release_series[0].title)
                    action= "-" # TODO probably set it to open the details page
                    day = _("day") if new_release_movies_span.days == 1 else _("days")
                    # TRANSLATOR: {title} is the title of the series and {new_release_series_span.days} the number of days, {day} is either day or days
                    body = _(f"A new episode of {new_release_series[0].title} was released {new_release_series_span.days} {day} ago.")
                else:
                    title = _(f"New release for {len(new_release_series)} series on your watchlist")
                    action= "-" # TODO set to main view with category new releases on top
                    string = ", ".join(new.title for new in new_release_series)
                    # TRANSLATOR: {string} will be list of series seperated by a comma
                    body = _(f"The series are {string}.")

            if soon_release_series:
                if len(soon_release_series) == 1:
                    title = _(f"{soon_release_series[0].title} will have a release soon")
                    action= "-" # TODO probably set it to open the details page
                    day = _("day") if new_release_movies_span.days == 1 else _("days")
                    # TRANSLATOR: {title} is the title of the series and {new_release_series_span.days} the number of days, {day} is either day or days
                    body = _(f"A new episode will release in {soon_release_series_span.days} {day}.")
                else:
                    title = _(f"{len(soon_release_series)} series on your watchlist will have a new episode soon")
                    action= "-" # TODO  do not know
                    string = ", ".join(soon.title for soon in soon_release)
                    # TRANSLATOR: {string} will be list of all series affected seperated by a comma
                    body = _(f"The series are {string}.")

            if out_of_production_series:
                if len(out_of_production_series) == 1:
                    title =  _(f"{out_of_production_series[0].title} has gone out of production")
                    action= "-" # TODO probably set it to open the details page
                    # TRANSLATOR: {title} is the title of the series 
                    body = _(f"We hope {out_of_production_series[0].title} has come to an satisfiying ending.") # TODO tone okay?
                else:
                    title =  _(f"{len(out_of_production_series)} series of your watchlist have gone out of production")
                    action= "-" # TODO probably just open main_view on series
                    string = ", ".join(out.title for out in out_of_production_series)
                    # TRANSLATOR: {string} will be list of all series affected seperated by a comma
                    body = _(f"The series are {string}." )


            if new_release_movies:
                if len(new_release_movies) == 1:
                    title = _(f"{new_release_movies[0].title} has had its release!")
                    action= "-" # TODO probably set it to open the details page
                    day = _("day") if new_release_movies_span.days == 1 else _("days")
                    # TRANSLATOR: {title} is the title of the series and {new_release_series_span.days} the number of days, {day} is either day or days
                    body = _(f"{new_release_movies[0].title} was released {new_release_movies_span.days} {day} ago.") #
                else:
                    title = _(f"{len(new_release_movies)} movies on your watchlist have had their releases.")
                    action= "-" # TODO set to main view with category new releases on top
                    string = ", ".join(new.title for new in new_release_movies)
                    # TRANSLATOR: {string} will be list of all series affected seperated by a comma
                    body = _(f"The movies are {string}.")

            if soon_release_movies:
                if len(soon_release_movies) == 1:
                    title = _(f"{soon_release_movies[0].title} will have its release soon!")
                    action= "-" # TODO probably set it to open the details page
                    day = _("day") if new_release_movies_span.days == 1 else _("days")
                    # TRANSLATOR: {title} is the title of the series and {new_release_series_span.days} the number of days, {day} is either day or days
                    body = _(f"{soon_release_movies[0].title} will have its release in {soon_release_movies_span.days} {day}.")
                else:
                    title = _(f"{len(soon_release_movies)} movies on your watchlist will have their releases soon")
                    action= "-" # TODO  do not know
                    string = ", ".join(soon.title for soon in soon_release_movies)
                    # TRANSLATOR: {string} will be list of all series affected seperated by a comma
                    body = _(f"The series are {string}.")

            notification = Gio.Notification.new(title)
            notification.set_default_action(action) 
            notification.set_body(body)
            self.app.send_notification(None, notification)       
        else:
            count_movies = len(new_release_movies) + len(soon_release_movies)
            count_series = len(new_release_series) + len(soon_release_series) + len(out_of_production_series)
            # TRANSLATOR: count_movies + count_series is the number of affected items
            title = _(f"{count_movies + count_series} items of your watchlist have an update")
            action= "-" # TODO  do not know

            string_body_movies = ''
            string_body_series = ''
            movie = _("movie") if count_movies == 1 else _("movies")
            serie = _("serie") if count_series == 1 else _("series")
            if count_movies > 0:
                string_body_movies = f"{count_movies} {movie}"
            if count_series > 0:
                string_body_movies = f"{count_series} {serie}"
            connector = _("and") if count_movies > 0 and count_series > 0 else ''
            # TRANSLATOR: string_body_movies could be "(digit) movie(s)" or empty; connector could be "and" or empty ; string_body_series could be "(digit) series(s)" or empty
            body = _(f"These updates affect {string_body_movies} {connector} {string_body_series}.")

            notification = Gio.Notification.new(title)
            notification.set_default_action(action) 
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


    def refresh(self) -> None:
        """
        Refreshes the visible window.

        Args:
            None

        Returns:
            None
        """
        
        if self._tab_stack.get_visible_child_name() == 'movies':
            self._tab_stack.get_child_by_name('movies').refresh_view()
            logging.info('Refreshed movies tab')
            self._needs_refresh = 'series'
        else:
            self._tab_stack.get_child_by_name('series').refresh_view()
            logging.info('Refreshed TV series tab')
            self._needs_refresh = 'movies'
