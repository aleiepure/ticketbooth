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

    def __init__(self):
        super().__init__()
        local.update_series_table()
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

        if last_check + timedelta(seconds=20) < datetime.now():
            logging.info('Starting automatic notification list update...')
            BackgroundQueue.add(
                activity=BackgroundActivity(
                    activity_type=ActivityType.UPDATE,
                    title=C_('Background activity title',
                                'Automatic update of notification'),
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
                    new_serie = SeriesModel(tmdb.get_serie(serie.id))
                    local.update_series(old=serie,serie=new_serie)

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
        series = local.get_all_watchlist()

        new_release = []
        soon_release = []
        out_of_production = []

        for serie in series:
            
            last_air_date = datetime.strptime(serie.last_air_date, '%Y-%m-%d')

            # Get the latest info for the series from TMDB
            new_serie = SeriesModel(tmdb.get_serie(serie.id))
            new_last_air_date = datetime.strptime(new_serie.last_air_date, '%Y-%m-%d')
            if new_serie.next_air_date != '':
                new_next_air_date = datetime.strptime(new_serie.next_air_date, '%Y-%m-%d')
            else:
                new_next_air_date = datetime.today() + timedelta(days = 10) # create bogus next air date if it does not exist
                
            # Check if the latest release is newer than the last saved in the database -> new release has come out.
            if last_air_date < new_last_air_date:
                # Set the new release status and add the series to the new releases list
                local.set_new_release_status(serie.id, True)
                new_release.append(new_serie)
                new_release_span = new_last_air_date - datetime.now() #we only save one, since we do not use it if more than one series has a new release
            
            # Check if the next air date is set to soon (6 days in the future)
            if datetime.now() + timedelta(days=6) > new_next_air_date:
                local.set_soon_release_status(serie.id, True)
                # if we also detect a considerable amount of time bewteen epsidoe notify user that the series has new releases coming soon.
                # 3 weeks are chosen to include the new streaming release model of two chunks a month apart but not spam the user for weekly or bi-weekly releases
                if new_next_air_date - timedelta(days=20) > last_air_date:
                    soon_release.append(new_serie)
                    soon_release_span =  datetime.now() - new_last_air_date
            
            # Check if the series went from in production to not in production
            if serie.in_production == 1 and new_serie.in_production == 0:
                out_of_production.append(new_serie)

            local.update_series(serie, new_serie)

        if new_release:
            if len(new_release) == 1:
                title = "New release for " + new_release[0].title
                action= "-" # TODO probably set it to open the details page
                body = f"A new episode was released {new_release_span} days ago"
                notification = Gio.Notification.new(title)
                notification.set_default_action(action) 
                notification.set_body(body)
                self.app.send_notification(None, notification)
            else:
                title = "New release for " + len(new_release) + " series on your watchlist"
                action= "-" # TODO set to main view with category new releases on top
                body = f"Click to see all new releases"
                notification = Gio.Notification.new(title)
                notification.set_default_action(action) 
                notification.set_body(body)
                self.app.send_notification(None, notification)

        if soon_release:
            if len(soon_release) == 1:
                title = "New release for " + soon_release[0].title
                action= "-" # TODO probably set it to open the details page
                body = f"A new episode will release in {soon_release_span.days} days"
                notification = Gio.Notification.new(title)
                notification.set_default_action(action) 
                notification.set_body(body)
                self.app.send_notification(None, notification)
            else:
                title = len(new_release) + " series on your watchlist will have a new episode soon"
                action= "-" # TODO  do not know
                body = f"Click to see all new releases"
                notification = Gio.Notification.new(title)
                notification.set_default_action(action) 
                notification.set_body(body)
                self.app.send_notification(None, notification)

        if out_of_production:
            if len(out_of_production) == 1:
                title =  f"{out_of_production[0].title} has gone out of production"
                action= "-" # TODO probably set it to open the details page
                body = f"We hope {out_of_production[0].title} has come to an satisfiying ending." # TODO tone okay?
                notification = Gio.Notification.new(title)
                notification.set_default_action(action) 
                notification.set_body(body)
                self.app.send_notification(None, notification)
            if len(out_of_production) == 1:
                title =  f"{len(out_of_production)} series of your watchlist have gone out of production"
                action= "-" # TODO probably just open main_view on series
                string = ", ".join(out.title for out in out_of_production)
                body = f"The series are {string}" #if somebody is unfortunate enough to have more than 5 series cancelled then this will probably overflow
                notification = Gio.Notification.new(title)
                notification.set_default_action(action) 
                notification.set_body(body)
                self.app.send_notification(None, notification)
            
        self.refresh()


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
