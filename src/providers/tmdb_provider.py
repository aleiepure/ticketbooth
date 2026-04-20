# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os

import tmdbsimple as tmdb

from .. import shared  # type: ignore
from requests import HTTPError

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

    @staticmethod
    def get_request_token() -> str:
        """
        Get a new request token from TMDB. With this request token you can get a Session ID

        Args:
            None

        Returns:
            str with the request token or none if a error has occured
        """
        try:
            token = tmdb.Authentication().token_new()
            return token['request_token']
        except (tmdb.base.APIKeyError, HTTPError):
            return None

    @staticmethod
    def get_session(request_token:str) -> str | None:
        """
        Get a new Session ID from TMDB. Session ID gives full access to a TMDB Account The Session ID is saved in the schema at the moment.

        Args:
            string with the request token

        Returns:
            str with the session ID or None if an error has occured
        """
        try:
            session = tmdb.Authentication().session_new(request_token = request_token)
            shared.schema.set_string('tmdb-session-id', session['session_id'])
            return session['session_id']
        except (tmdb.base.APIKeyError, HTTPError):
            return None

    @staticmethod
    def make_account(session_id: str | None = None) -> tmdb.Account | None:
        """
        Make Account by calling TMDB.Account.info(). This account object can now be used to access TMDB account.

        Args:
            string with the session ID or None

        Returns:
            Account object or None if an error has occured
        """
        if not session_id:
            session_id = shared.schema.get_string('tmdb-session-id')
        account = tmdb.Account(session_id)
        try: 
            account.info()
            return account
        except (tmdb.base.APIKeyError, HTTPError):
            return None

    @staticmethod
    def delete_session(session_id: str | None = None) -> str | None:
        """
            Deletes the session ID from TMDB, removing access. Setting schema string tmdb-session-id is job of caller.

        Args:
            string with the session ID or None

        Returns:
            String to signal success or None if an error has occured
        """
        try:
            kwargs = {'session_id': shared.schema.get_string('tmdb-session-id')}
            session = tmdb.Authentication().session_delete(**kwargs)
            return 'success'
        except (tmdb.base.APIKeyError, HTTPError):
            return None  

    @staticmethod
    def get_TV_watchlist(account: tmdb.Account, page = 1, lang: str | None = None) -> dict | None:
        """
            Get TV watchlist of account given. 

        Args:
            Account (TMDBProvider.Account): Account object from make_account()
            page (int): Number of page we want to get, one page is normally 20 series long (optional) 
            lang: the prefered language for the results (optional)

        Returns:
            Dict with result (see for more details: https://developer.themoviedb.org/reference/account-watchlist-tv) or None if an error has occured
        """
        if not lang:
            lang = shared.schema.get_string('tmdb-lang')
        try: 
            series = account.watchlist_tv(sort_by = 'created_at.desc', language = lang, page = page)
            return series
        except (tmdb.base.APIKeyError, HTTPError):
            return None

    @staticmethod
    def get_movie_watchlist(account: tmdb.Account, page = 1, lang: str | None = None) -> dict | None:
        """
            Get movies watchlist of account given. 

        Args:
            Account (TMDBProvider.Account): Account object from make_account()
            page (int): Number of page we want to get, one page is normally 20 series long (optional) 
            lang: the prefered language for the results (optional)

        Returns:
            Dict with result (see for more details: https://developer.themoviedb.org/reference/account-watchlist-movies) or None if an error has occured
        """
        if not lang:
            lang = shared.schema.get_string('tmdb-lang')
        try:
            series = account.watchlist_movies(sort_by = 'created_at.desc', language = lang, page = page)
            return series
        except (tmdb.base.APIKeyError, HTTPError):
            return None

    @staticmethod
    def add_content_to_tmdb_watchlist(account, movie: bool, id: int, add = True) -> str | None:
        """
            Add content to TMDB watchlist of Account.
            
        Args:
            Account (TMDBProvider.Account): Account object from make_account()
            id (int): Number of page we want to get, one page is normally 20 series long (optional) 
            add: If true content gets added to TMDB watchlist and vice versa

        Returns:
            String to signal success or None if an error has occured
        """
        kwargs = {
            'media_type': 'movie' if movie else 'tv',
            'media_id': id,
            'watchlist': add,
        }
        try: 
            result = account.watchlist(**kwargs)
            return 'success'
        except (tmdb.base.APIKeyError, HTTPError):
            return None

    