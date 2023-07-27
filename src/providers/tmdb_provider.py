# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import glob
import os
from typing import Callable

import requests
import tmdbsimple as tmdb
from gi.repository import Gio, GObject

from .. import shared  # type: ignore


class TMDBProvider(GObject.Object):
    """
    This class provides methods to interface with the TMDB API.

    Properties:
        None

    Methods:
        search(query: str, lang: str): Searches the API for the given query
        get_languages(): Retrieves all available languages usable with the API
    """
    __gtype_name__ = 'TMDBProvider'

    tmdb.API_KEY = os.environ.get('TMDB_KEY')

    _path = ''

    def __init__(self):
        super().__init__()

    @staticmethod
    def search(query: str, lang: str = shared.schema.get_string('tmdb-lang')) -> dict:
        """
        Searches the API for the given query.

        Args:
            query (str): a query to lookup
            lang (str): the prefered language for the results (optional)

        Returns:
            dict containg the API result.
        """

        return tmdb.Search().multi(query=query, language=lang)

    @staticmethod
    def get_languages() -> dict:
        """
        Retrieves all available languages usable with the API

        Args:
            None

        Returns:
            dict containg the API result.
        """

        return tmdb.Configuration().languages()
