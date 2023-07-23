# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import GObject


class SearchResultModel(GObject.GObject):
    __gtype_name__ = 'SearchResultModel'

    tmdb_id = GObject.Property(type=int)
    title = GObject.Property(type=str, default='')
    media_type = GObject.Property(type=str, default='')
    poster_path = GObject.Property(type=str, default='')
    description = GObject.Property(type=str, default='')

    def __init__(self, d=None):
        super().__init__()

        if d is not None:
            self.tmdb_id = d['id']
            self.media_type = d['media_type']
            self.poster_path = d['poster_path']
            self.description = d['overview']

            if self.media_type == 'movie':
                self.title = d['title']
            elif self.media_type == 'tv':
                self.title = d['name']
