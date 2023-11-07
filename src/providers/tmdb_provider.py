# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os

import tmdbsimple as tmdb

from .. import shared  # type: ignore


class TMDBProvider:
    """
    This class provides methods to interface with the TMDB API.

    Properties:
        None

    Methods:
        search(query: str, lang: str or None): Searches the API for the given query
        get_languages(): Retrieves all available languages usable with the API
        get_movie(id: int, lang: str): Retrieves general information about a movie.
        get_serie(id: int, lang: str): Retrieves general information about a tv series.
        get_season_episodes(id: int, series:int, lang: str): Retrieves information about the episodes in a season.
    """

    if shared.schema.get_boolean('use-own-tmdb-key'):
        tmdb.API_KEY = shared.schema.get_string('own-tmdb-key')
    else:
        tmdb.API_KEY = os.environ.get('TMDB_KEY')

    def __init__(self):
        super().__init__()

    @staticmethod
    def search(query: str, lang: str | None = None) -> dict:
        """
        Searches the API for the given query.

        Args:
            query (str): a query to lookup
            lang (str or None): the prefered language for the results (ISO 639-1 format)

        Returns:
            dict containg the API result.
        """

        if not lang:
            lang = shared.schema.get_string('tmdb-lang')

        return tmdb.Search().multi(query=query, language=lang, include_adult=False)

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

    @staticmethod
    def get_movie(id: int, lang: str | None = None) -> dict:
        """
        Retrieves general information about the movie with the provided id.

        Args:
            id (int): id of the movie
            lang (str): the prefered language for the results (optional)

        Returns:
            dict containg the API result.
        """
        if not lang:
            lang = shared.schema.get_string('tmdb-lang')

        return tmdb.Movies(id).info(language=lang)

    @staticmethod
    def get_serie(id: int, lang: str | None = None) -> dict:
        """
        Retrieves general information about the tv series with the provided id.

        Args:
            id (int): id of the tv series
            lang (str): the prefered language for the results (optional)

        Returns:
            dict containg the API result
        """
        if not lang:
            lang = shared.schema.get_string('tmdb-lang')
            
        return tmdb.TV(id).info(language=lang)

    @staticmethod
    def get_season_episodes(id: int, season: int, lang: str | None = None) -> dict:
        """
        Retrieves information about the episodes in a season for the specified tv series.

        Args:
            id (int): id of the tv series
            season (int): season number
            lang (str): the prefered language for the results (optional)

        Returns:
            dict containg the API result.
        """

        if not lang:
            lang = shared.schema.get_string('tmdb-lang')

        return tmdb.TV_Seasons(id, season).info(language=lang)['episodes']

    @staticmethod
    def set_key(key: str) -> None:
        """
        Sets the API in use.

        Args:
            key (str): key to use

        Returns:
            None
        """

        tmdb.API_KEY = key

    @staticmethod
    def get_key() -> str:
        """
        Gets the API in use.

        Args:
            None

        Returns:
            str with the key in use
        """

        return tmdb.API_KEY

    @staticmethod
    def get_builtin_key() -> str:
        """
        Gets the builtin API key.

        Args:
            None

        Returns:
            str with the builtin key
        """

        return os.environ.get('TMDB_KEY')  # type: ignore
