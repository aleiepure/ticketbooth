# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import locale
import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta
from gettext import gettext as _

from gi.repository import Adw, Gio, GLib, GObject, Gtk

from .. import shared  # type: ignore
from ..models.movie_model import MovieModel
from ..models.series_model import SeriesModel
from ..providers.local_provider import LocalProvider as local
from ..providers.tmdb_provider import TMDBProvider as tmdb

@Gtk.Template(resource_path=shared.PREFIX + '/ui/views/db_update_view.ui')
class DbUpdateView(Adw.Bin):
    """
    This class represents the initial setup the app needs to offer full fuctionality.

    Properties:
        None

    Methods:
        None

    Signals:
        exit: emited when the view has completed its operations, either the required data was successfully downloaded \
              or the user requested "offline mode"
    """

    __gtype_name__ = 'dbUpdateView'

    _progress_bar = Gtk.Template.Child()
    _update_progress_page = Gtk.Template.Child()
    _notification_question = Gtk.Template.Child()
    _activate_btn = Gtk.Template.Child()
    _deactivate_btn = Gtk.Template.Child()
    _carousel = Gtk.Template.Child()
    _offline_btn = Gtk.Template.Child()
    _retry_check_btn = Gtk.Template.Child()

    __gsignals__ = {
        'exit': (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    _cancellable = Gio.Cancellable.new()

    def __init__(self):
        super().__init__()

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data: object | None) -> None:
        """
        Callback for "map" signal.
        Creates the directories and tables in the local db, sets the tmdb results language based on the locale, and attempts to download required data if connected to the Internet.

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """
        

        logging.info('Updating Database...')

        local.update_movies_table()
        local.update_series_table()

        logging.info('Added new Columns to Database')

        if shared.schema.get_boolean('offline-mode'):
            self.emit('exit')
        logging.info('Refetching Data from TMDB...')
        self.task = Gio.Task.new()
        self.task.run_in_thread(
            lambda*_:self._fetch_data_from_tmdb()
        )
       

    @Gtk.Template.Callback('_on_offline_btn_clicked')
    def _on_offline_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for "clicked" signal.
        Stops the background network check and sets the app in offline mode. An option to retry on next launch is
        provided.

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        self._cancellable.cancel()

        shared.schema.set_boolean('offline-mode', True)
        logging.info('[Update] Offline mode enabled')
        if not self._retry_check_btn.get_active():
            shared.schema.set_boolean('db-needs-update', False)
            logging.info('[Update] Database update partially complete')

        logging.info('[Update] Database update not completed, retrying on next run')
        self.emit('exit')

    def _fetch_data_from_tmdb(self) :
        with sqlite3.connect(shared.db) as connection: 

            movies = local.get_all_movies()
            series = local.get_all_series()
            
            total = len(movies) + len(series)
            counter = 0
            for movie in movies:
                if not movie.manual:
                    new_movie = MovieModel(tmdb.get_movie(movie.id))
                    #Check if the soon_release flag should be set, that is the case if the movie is set to release in less than 14 days
                    if len(movie.release_date) > 0 and datetime.strptime(movie.release_date, '%Y-%m-%d') < datetime.now() + timedelta(days=14): # TODO make this a variable and sync with main_view.py
                        #Writing to the local db since update_movie updates entry of the local db
                        local.set_soon_release_status(movie.id, True, True)
                    local.update_movie(movie, new_movie)
                    counter += 1
                    self._progress_bar.set_fraction(counter/total)

            for serie in series:
                if not serie.manual:
                    new_serie = SeriesModel(tmdb.get_serie(serie.id))
                     #Check if the soon_release flag should be set, that is the case if the next episode is less than 7 days away
                    compare_date = new_serie.next_air_date
                    if len(compare_date) > 0 and datetime.strptime(compare_date, '%Y-%m-%d') < datetime.now() + timedelta(days=7): # TODO make this a variable and sync with main_view.py
                        #Writing to variable since update_series deletes local db entry and creates a new entry with flags from argument
                        serie.soon_release = True
                    local.update_series(serie, new_serie)
                    counter += 1
                    self._progress_bar.set_fraction(counter/total)

        logging.info('Fetched Data from TMDB.')

        #Go to next page in the carousel
        index = int(self._carousel.get_position())
        next_page = self._carousel.get_nth_page(index + 1)
        self._carousel.scroll_to(next_page, True)
          
    @Gtk.Template.Callback('_on_deactivate_btn_clicked')
    def _on_btn_deactivate_clicked(self, user_data: object | None) -> None:
        """
        Callback for "clicked" signal.
        Sets all activate_notification to false in local db and exits carousel

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """
        local.reset_activate_notification()
        shared.schema.set_boolean('db-needs-update', False)
        logging.debug(f'db update dialog: confim, deactivate notifications')
        self.emit('exit')

    @Gtk.Template.Callback('_on_activate_btn_clicked')
    def _on_btn_activate_clicked(self, user_data: object | None) -> None:
        """
        Callback for "clicked" signal.
        Exits carousel.

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """
        shared.schema.set_boolean('db-needs-update', False)
        self.emit('exit')