# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import re

from gi.repository import GObject


class SearchResultModel(GObject.GObject):
    """
    This class represents the object returned from the TMDB search endpoint.

    Properties:
        title (str): content's title
        year (str): content's release year
        description (str): content's description
        poster_path (str): API endpoint for the content poster
        tmdb_id (int): content's unique id in the API
        media_type (str): content's media type

    Methods:
        None

    Signals:
        None
    """

    __gtype_name__ = 'SearchResultModel'

    title = GObject.Property(type=str, default='')
    year = GObject.Property(type=str, default='')
    description = GObject.Property(type=str, default='')
    poster_path = GObject.Property(type=str, default='')
    tmdb_id = GObject.Property(type=int, default=0)
    media_type = GObject.Property(type=str, default='')

    def __init__(self, d=None):
        super().__init__()

        if d is not None:
            self.tmdb_id = d['id']
            self.poster_path = d['poster_path']
            self.description = re.sub(r'\s{2}', ' ', d['overview'])

            if d['media_type'] == 'movie':
                self.media_type = d['media_type']
                self.title = d['title']
                self.year = d['release_date'][0:4]
            elif d['media_type'] == 'tv':
                self.media_type = d['media_type']
                self.title = d['name']
                self.year = d['first_air_date'][0:4]
