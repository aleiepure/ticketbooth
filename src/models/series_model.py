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
        manual (bool): if the series is added manually
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

    Methods:
        None

    Signals:
        None
    """

    __gtype_name__ = 'SeriesModel'

    add_date = GObject.Property(type=str, default='')
    backdrop_path = GObject.Property(type=str, default='')
    created_by = GObject.Property(type=GLib.strv_get_type())
    episodes_number = GObject.Property(type=int, default=0)
    genres = GObject.Property(type=GLib.strv_get_type())
    id = GObject.Property(type=str, default='')
    in_production = GObject.Property(type=bool, default=True)
    manual = GObject.Property(type=bool, default=False)
    original_language = GObject.Property(type=LanguageModel)
    original_title = GObject.Property(type=str, default='')
    overview = GObject.Property(type=str, default='')
    poster_path = GObject.Property(type=str, default='')
    release_date = GObject.Property(type=str, default='')
    seasons_number = GObject.Property(type=int, default=0)
    seasons = GObject.Property(type=object)
    status = GObject.Property(type=str, default='')
    tagline = GObject.Property(type=str, default='')
    title = GObject.Property(type=str, default='')
    watched = GObject.Property(type=bool, default=False)

    def __init__(self, d=None, t=None):
        super().__init__()

        if d is not None:
            self.add_date = datetime.now()
            self.backdrop_path = self._download_background(d['backdrop_path'])
            self.created_by = self._parse_creators(api_dict=d['created_by'])
            self.episodes_number = d['number_of_episodes']
            self.genres = self._parse_genres(api_dict=d['genres'])
            self.id = d['id']
            self.in_production = d['in_production']
            self.manual = False
            self.original_language = local.LocalProvider.get_language_by_code(
                d['original_language'])  # type: ignore
            self.original_title = d['original_name']
            self.overview = re.sub(r'\s{2}', ' ', d['overview'])
            self.poster_path = self._download_poster(d['poster_path'])
            self.release_date = d['first_air_date']
            self.seasons_number = d['number_of_seasons']
            self.seasons = self._parse_seasons(d['seasons'])
            self.status = d['status']
            self.tagline = d['tagline']
            self.title = d['name']
            self.watched = False
        else:
            self.add_date = t[0]  # type: ignore
            self.backdrop_path = t[1]  # type: ignore
            self.created_by = self._parse_creators(db_str=t[2])  # type: ignore
            self.episodes_number = t[3]  # type: ignore
            self.genres = self._parse_genres(db_str=t[4])  # type: ignore
            self.id = t[5]  # type: ignore
            self.in_production = t[6]  # type: ignore
            self.manual = t[7]  # type: ignore
            self.original_language = local.LocalProvider.get_language_by_code(
                t[8])  # type: ignore
            self.original_title = t[9]  # type: ignore
            self.overview = t[10]  # type: ignore
            self.poster_path = t[11]  # type: ignore
            self.release_date = t[12]  # type: ignore
            self.seasons_number = t[13]  # type: ignore
            self.status = t[14]  # type: ignore
            self.tagline = t[15]  # type: ignore
            self.title = t[16]  # type: ignore
            self.watched = t[17]  # type: ignore

            if len(t) == 19:  # type: ignore
                self.seasons = t[18]  # type: ignore
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
