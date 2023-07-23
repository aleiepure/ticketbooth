# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import glob
from typing import Callable

import requests
from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk

from .. import shared  # type: ignore


@Gtk.Template(resource_path=shared.PREFIX + '/ui/widgets/poster_tile.ui')
class PosterTile(Gtk.Box):
    __gtype_name__ = 'PosterTile'

    _poster_btn = Gtk.Template.Child()
    _spinner = Gtk.Template.Child()
    _picture = Gtk.Template.Child()
    _title_lbl = Gtk.Template.Child()

    # Properties
    title = GObject.Property(type=str, default='')
    tmdb_id = GObject.Property(type=int, default=0)
    poster_path = GObject.Property(type=str, default='')

    def get_poster_file(self):
        """
        Get the associated poster image. Files can be retrieved from Internet
        or from local storage. In case no image is found, a blank poster will
        be shown.

        Args:
            None

        Returns:
            Gio.File containing the right image.
        """

        if self.poster_path:
            self._spinner.set_visible(True)
            self._spinner.set_spinning(True)
            self._get_poster_async(self, self._on_get_poster_done)
        else:
            return Gio.File.new_for_uri(f'resource://{shared.PREFIX}/blank_poster.jpg')

    def __init__(self):
        super().__init__()
        self.set_property('css-name', 'poster_tile')

        # Property binding
        self.bind_property('title', self._title_lbl, 'label', GObject.BindingFlags.SYNC_CREATE)

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data):
        self._picture.set_file(self.get_poster_file())

    def _get_poster_async(self, caller: GObject.Object, callback: Callable):
        Gio.Task.new(caller, None, callback, None).run_in_thread(self._get_poster_thread)

    def _get_poster_thread(self, task: Gio.Task, source_object: GObject.Object, task_data: object, cancelable: Gio.Cancellable):
        if task.return_error_if_cancelled():
            return
        outcome = self._get_poster()
        task.return_value(outcome)

    def _get_poster(self) -> Gio.File:
        files = glob.glob(f'{self.poster_path[1:-4]}.*.jpg', root_dir=GLib.get_tmp_dir())
        if files:
            return Gio.File.new_for_path(GLib.get_tmp_dir() + '/' + files[0])
        else:
            # TODO: add option to clean cached files
            url = f'https://image.tmdb.org/t/p/original{self.poster_path}'
            r = requests.get(url)
            tmp_file = Gio.File.new_tmp(f'{self.poster_path[1:-4]}.XXXXXX.jpg')[0]
            if r.status_code == 200:
                with open(tmp_file.get_path(), 'wb') as f:
                    f.write(r.content)
            return tmp_file

    def _get_poster_async_finish(self, result: Gio.AsyncResult, caller: GObject.Object):
        if not Gio.Task.is_valid(result, caller):
            return -1
        return result.propagate_value().value

    def _on_get_poster_done(self, source_widget: GObject.Object, result: Gio.AsyncResult, user_data: GObject.GPointer):
        poster = self._get_poster_async_finish(result, self)
        self._spinner.set_spinning(False)
        self._spinner.set_visible(False)
        self._picture.set_file(poster)
