# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import glob
from gettext import gettext as _

import requests
from gi.repository import Gio, GLib, GObject, Gtk

from .. import shared  # type: ignore
from ..providers.local_provider import LocalProvider as local


@Gtk.Template(resource_path=shared.PREFIX + '/ui/widgets/search_result_row.ui')
class SearchResultRow(Gtk.ListBoxRow):
    """
    Widget used to show a search result from TMDB in the search window.

    Properties:
        title (str): a title
        year (str): a release year
        description (str): a description
        poster_path (str): an API endpoint for a poster
        tmdb_id (int): a TMDB id
        media_type (str): a media type
        year_visible (bool): whether or not to show the release year

    Methods:
        None

    Signals:
        None
    """

    __gtype_name__ = 'SearchResultRow'

    _poster_picture = Gtk.Template.Child()
    _spinner = Gtk.Template.Child()
    _media_type_lbl = Gtk.Template.Child()
    _add_btn = Gtk.Template.Child()

    tmdb_id = GObject.Property(type=int, default=0)
    title = GObject.Property(type=str, default='')
    year = GObject.Property(type=str, default='')
    description = GObject.Property(type=str, default='')
    poster_path = GObject.Property(type=str, default='')
    media_type = GObject.Property(type=str, default='')
    year_visible = GObject.Property(type=bool, default=False)

    def __init__(self):
        super().__init__()

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data: object | None) -> None:
        """
        Callback for the "map" signal.
        Sets the visibility of the release year, the media type label and the poster to show.
        Additionally checks if the content is already in db and disables the 'add' button.

        Args:
            user_data (object or None): user data passed to the callback

        Returns:
            None
        """

        if self.year:
            self.year_visible = True

        if self.media_type == 'movie':
            self._media_type_lbl.set_label(_('Movie'))
        else:
            self._media_type_lbl.set_label(_('TV Series'))

        self._spinner.set_visible(True)
        self._poster_picture.set_file(self._get_poster_file())

        GLib.Thread.new(None, self._check_in_db_thread, None)

    def _check_in_db_thread(self, thread_data):
        if local.get_movie_by_id(self.tmdb_id):
            self._add_btn.set_label(_('Already in your whatchlist'))
            self._add_btn.set_icon_name('check-plain')
            self._add_btn.set_sensitive(False)

    def _get_poster_file(self) -> None | Gio.File:
        """
        Get the associated poster image. Files can be retrieved from Internet
        or from local storage if already downloaded in the past. In case no image is found, a blank poster will
        be returned.
        The retrieval is done asynchronously.

        Args:
            None

        Returns:
            None or a Gio.File containing an image
        """
        if self.poster_path:
            Gio.Task.new(self, None, self._on_get_poster_done, None).run_in_thread(self._get_poster_thread)
        else:
            self._spinner.set_visible(False)
            return Gio.File.new_for_uri(f'resource://{shared.PREFIX}/blank_poster.jpg')

    def _on_get_poster_done(self, source_widget: GObject.Object | None, result: Gio.AsyncResult,
                            user_data: object | None) -> None:
        """
        Callback for the async poster retrieval.
        Hides the spinner and shows the poster.

        Args:
            source (GObject.Object or None): the object the asynchronous operation was started with.
            result (Gio.AsyncResult): a Gio.AsyncResult
            user_data (object or None): user data passed to the callback

        Returns:
            None
        """

        poster = self._get_poster_file_finish(result, self)
        self._spinner.set_visible(False)
        self._poster_picture.set_file(poster)

    @Gtk.Template.Callback('_on_add_btn_clicked')
    def _on_add_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for "clicked" signal.
        Invokes a thread to insert the content into the local db.

        Args:
            user_data (object or None): user data passed to the callback

        Returns:
            None
        """

        GLib.Thread.new(f'Adding {self.tmdb_id}', self._add_content_to_db_thread, None)

    def _add_content_to_db_thread(self, thread_data: object | None) -> None:
        """
        Adds the associated title to the corresponding table in the db. Disables the 'add' button when done

        Args:
            thread_data (object or None): data passed to the thread
        """

        local.add_content(tmdb_id=self.tmdb_id, media_type=self.media_type)
        self._add_btn.set_label(_('Already in your whatchlist'))
        self._add_btn.set_icon_name('check-plain')
        self._add_btn.set_sensitive(False)

    def _get_poster_thread(self, task: Gio.Task, source_object: GObject.Object, task_data: object | None,
                           cancelable: Gio.Cancellable | None) -> None:
        """
        Wraper around a blocking function to run it as a non-blocking.

        Args:
            task (Gio.Task): the Gio.Task
            source_object (GObject.Object): task's source object
            task_data (object or None): task's task data
            cancellable (Gio.Cancellable or None): task's Gio.Cancellable, or None

        Returns:
            None
        """

        if task.return_error_if_cancelled():
            return
        outcome = self._get_poster()
        task.return_value(outcome)

    def _get_poster(self) -> Gio.File:
        """
        Returns the poster file from cached data, downloading it if necessary.

        Args:
            None

        Returns:
            Gio.File containing the poster
        """

        files = glob.glob(f'{self.poster_path[1:-4]}.jpg', root_dir=shared.cache_dir)
        if files:
            return Gio.File.new_for_path(f'{shared.cache_dir}/{files[0]}')
        else:
            url = f'https://image.tmdb.org/t/p/w500{self.poster_path}'
            r = requests.get(url)
            if r.status_code == 200:
                with open(f'{shared.cache_dir}{self.poster_path}', 'wb') as f:
                    f.write(r.content)
            return Gio.File.new_for_path(f'{shared.cache_dir}{self.poster_path}')

    def _get_poster_file_finish(self, result: Gio.AsyncResult, caller: GObject.Object) -> int | Gio.File:
        """
        Finishes the async operation returning the value.

        Args:
            result: a Gio.AsyncResult
            caller: the caller of the task

        Returns:
            int or Gio.File
        """

        if not Gio.Task.is_valid(result, caller):
            return -1
        return result.propagate_value().value
