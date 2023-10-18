# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import glob
import re
from datetime import datetime
from typing import List

import requests
from gi.repository import GLib, GObject
from PIL import Image, ImageFilter

import src.providers.local_provider as local

from .. import shared  # type: ignore
from ..models.language_model import LanguageModel
from ..models.season_model import SeasonModel


class SeriesModel(GObject.GObject):
    """
    This class represents a series object stored in the db.

    Properties:
        add_date (str): date of addition to the db (ISO format)
        backdrop_path (str): uri of the background image
        created_by (List[str]): list of creators
        episodes_number (int): number of total episodes
        genres (List[str]): list of genres
        id (str): series id
        in_production (bool): whether the series is still in production
        last_air_date (str): the date of the last aired episode
        manual (bool): if the series is added manually
        new_release (bool): whether the has seen a new release since the last check
        next_air_date (str) : used to notify user on upcoming releases
        original_language (LanguageModel): LanguageModel of the original language
        original_title (str): series title in original language
        overview (str): series overview
        poster_path (str): uri of the poster image
        release_date (str): first air date in YYYY-MM-DD format
        seasons_number (int): number of total seasons
        seasons (List[SeasonModel]): list of SeasonModels
        status (str): series status
        tagline (str): series tagline
        title (str): series title
        watched (bool): whether the series has been watched completely or not
        activate_notification (bool): whether the series should be checked for new releases

    Methods:
        None

    Signals:
        None
    """

    __gtype_name__ = 'SeriesModel'
    activate_notification = GObject.Property(type=bool, default=False)
    add_date = GObject.Property(type=str, default='')
    backdrop_path = GObject.Property(type=str, default='')
    created_by = GObject.Property(type=GLib.strv_get_type())
    episodes_number = GObject.Property(type=int, default=0)
    genres = GObject.Property(type=GLib.strv_get_type())
    id = GObject.Property(type=str, default='')
    in_production = GObject.Property(type=bool, default=True)
    last_air_date = GObject.Property(type=str, default='')
    manual = GObject.Property(type=bool, default=False)
    new_release = GObject.Property(type=bool, default=False)
    next_air_date = release_date = GObject.Property(type=str, default='')
    original_language = GObject.Property(type=LanguageModel)
    original_title = GObject.Property(type=str, default='')
    overview = GObject.Property(type=str, default='')
    poster_path = GObject.Property(type=str, default='')
    release_date = GObject.Property(type=str, default='')
    seasons_number = GObject.Property(type=int, default=0)
    seasons = GObject.Property(type=object)
    soon_release = GObject.Property(type=bool, default = False)
    status = GObject.Property(type=str, default='')
    tagline = GObject.Property(type=str, default='')
    title = GObject.Property(type=str, default='')
    watched = GObject.Property(type=bool, default=False)

    def __init__(self, d=None, t=None):
        super().__init__()
        
        if d is not None:
            self.activate_notification = False
            self.add_date = datetime.now()
            self.backdrop_path = self._download_background(d['backdrop_path'])
            self.created_by = self._parse_creators(api_dict=d['created_by'])
            self.episodes_number = d['number_of_episodes']
            self.genres = self._parse_genres(api_dict=d['genres'])
            self.id = d['id']
            self.in_production = d['in_production']
            self.last_air_date = d['last_air_date']
            self.manual = False
            self.new_release = False
            next_episode_to_air = d['next_episode_to_air']
            if next_episode_to_air == None: 
                self.next_air_date = "" 
            else: 
                self.next_air_date = next_episode_to_air['air_date']
            self.original_language = local.LocalProvider.get_language_by_code(
                d['original_language'])  # type: ignore
            self.original_title = d['original_name']
            self.overview = re.sub(r'\s{2}', ' ', d['overview'])
            self.poster_path = self._download_poster(d['poster_path'])
            self.release_date = d['first_air_date']
            self.seasons_number = d['number_of_seasons']
            self.seasons = self._parse_seasons(d['seasons'])
            self.soon_release = False
            self.status = d['status']
            self.tagline = d['tagline']
            self.title = d['name']
            self.watched = False
        else:
            self.activate_notification = t["activate_notification"]
            self.add_date = t["add_date"]  # type: ignore
            self.backdrop_path = t["backdrop_path"]  # type: ignore
            self.created_by = self._parse_creators(db_str=t["created_by"])  # type: ignore
            self.episodes_number = t["episodes_number"]  # type: ignore
            self.genres = self._parse_genres(db_str=t["genres"])  # type: ignore
            self.id = t["id"]  # type: ignore
            self.in_production = t["in_production"]  # type: ignore
            self.last_air_date = t["last_air_date"]
            self.manual = t["manual"]  # type: ignore
            self.new_release = t["new_release"]
            self.next_air_date = t["next_air_date"]
            self.original_language = local.LocalProvider.get_language_by_code(
                t["original_language"])  # type: ignore
            self.original_title = t["original_title"]  # type: ignore
            self.overview = t["overview"]  # type: ignore
            self.poster_path = t["poster_path"]  # type: ignore
            self.release_date = t["release_date"]  # type: ignore
            self.seasons_number = t["seasons_number"]  # type: ignore
            self.soon_release = t["soon_release"]  # type: ignore
            self.status = t["status"]  # type: ignore
            self.tagline = t["tagline"]  # type: ignore
            self.title = t["title"]  # type: ignore
            self.watched = t["watched"]  # type: ignore

            if self.seasons_number == 0:  # type: ignore
                self.seasons = []  # type: ignore
            else:
                self.seasons = local.LocalProvider.get_all_seasons(
                    self.id)  # type: ignore

    def _parse_genres(self, api_dict: dict = {}, db_str: str = '') -> List[str]:
        """
        Function to parse genres into a list of strings. Genres are provided by the TMDB API as a dict and are stored in the local db as a comma-separated string.
        Providing both arguments is an error.

        Args:
            from_api (dict): dict from TMDB API
            from_db (str): string from local db

        Returns:
            list of strings
        """

        genres = []

        if api_dict:
            for genre in api_dict:
                genres.append(genre['name'])
            return genres

        if db_str:
            return db_str.split(',')

        return genres

    def _parse_creators(self, api_dict: dict = {}, db_str: str = '') -> List[str]:
        """
        Function to parse the creators into a list of strings. Creators are provided by the TMDB API as a dict and are stored in the local db as a comma-separated string.
        Providing both arguments is an error.

        Args:
            from_api (dict): dict from TMDB API
            from_db (str): string from local db

        Returns:
            list of strings
        """

        creators = []
        if api_dict:
            for creator in api_dict:
                creators.append(creator['name'])
            return creators

        if db_str:
            return db_str.split(',')

        return creators

    def _parse_seasons(self, api_dict: dict) -> List[SeasonModel]:
        """
        Function to parse the seasons data into a list of SeasonModels.

        Args:
            api_dict (dict): dict from TMDB API

        Returns:
            list of SeasonModel
        """

        seasons = []

        for season in api_dict:
            seasons.append(SeasonModel(show_id=self.id, d=season))
        return seasons

    def _download_background(self, path: str) -> str:
        """
        Returns the uri of the background image on the local filesystem, downloading if necessary.

        Args:
            path (str): path to dowload from

        Returns:
            str with the uri of the background image
        """

        if not path:
            return ''

        files = glob.glob(f'{path[1:-4]}.jpg', root_dir=shared.background_dir)
        if files:
            return f'file://{shared.background_dir}/{files[0]}'

        url = f'https://image.tmdb.org/t/p/w500{path}'
        try:
            r = requests.get(url)
            if r.status_code == 200:
                with open(f'{shared.background_dir}{path}', 'wb') as f:
                    f.write(r.content)

                with Image.open(f'{shared.background_dir}{path}') as image:
                    image = (
                        image.convert('RGB')
                        .filter(ImageFilter.GaussianBlur(20))
                    )

                    image.save(f'{shared.background_dir}{path}', 'JPEG')

                return f'file://{shared.background_dir}{path}'
            else:
                return ''
        except (requests.exceptions.ConnectionError, requests.exceptions.SSLError):
            return ''

    def _download_poster(self, path: str) -> str:
        """
        Returns the uri of the poster image on the local filesystem, downloading if necessary.

        Args:
            path (str): path to dowload from

        Returns:
            str with the uri of the poster image
        """

        if not path:
            return f'resource://{shared.PREFIX}/blank_poster.jpg'

        files = glob.glob(f'{path[1:-4]}.jpg', root_dir=shared.poster_dir)
        if files:
            return f'file://{shared.poster_dir}/{files[0]}'

        url = f'https://image.tmdb.org/t/p/w500{path}'
        try:
            r = requests.get(url)
            if r.status_code == 200:
                with open(f'{shared.poster_dir}{path}', 'wb') as f:
                    f.write(r.content)
                return f'file://{shared.poster_dir}{path}'
            else:
                return f'resource://{shared.PREFIX}/blank_poster.jpg'
        except (requests.exceptions.ConnectionError, requests.exceptions.SSLError):
            return f'resource://{shared.PREFIX}/blank_poster.jpg'
