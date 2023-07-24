# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _

from gi.repository import GObject


class SearchResultModel(GObject.GObject):
    __gtype_name__ = 'SearchResultModel'

    title = GObject.Property(type=str, default='')
    year = GObject.Property(type=str, default='')
    description = GObject.Property(type=str, default='')
    poster_path = GObject.Property(type=str, default='')
    tmdb_id = GObject.Property(type=int)
    media_type = GObject.Property(type=str, default='')

    def __init__(self, d=None):
        super().__init__()

        if d is not None:
            self.tmdb_id = d['id']
            self.poster_path = d['poster_path']
            self.description = d['overview']

            if d['media_type'] == 'movie':
                self.media_type = _('Movie')
                self.title = d['title']
                self.year = d['release_date'][0:4]
            elif d['media_type'] == 'tv':
                self.media_type = _('TV Series')
                self.title = d['name']
                self.year = d['first_air_date'][0:4]
