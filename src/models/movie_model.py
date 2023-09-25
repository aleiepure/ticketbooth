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


class MovieModel(GObject.GObject):
    """
    This class rappresents a movie object stored in the db.

    Properties:
        add_date (str): date of addition to the db (ISO format)
        backdrop_path (str): path where the background image is stored
        budget (float): movie budget
        genres (List[str]): list of genres
        id (str): movie id
        manual (bool): if movie is added manually
        original_language (LanguageModel): LanguageModel of the original language
        original_title (str): movie title in original language
        overview (str): movie overview, usually the main plot
        poster_path (str): path where the backgroud poster is stored
        release_date (str): release date in YYYY-MM-DD format
        revenue (float): movie revenue
        runtime (int): movie runtime in minutes
        tagline (str): movie tagline
        status (str): movie status, usually released or planned
        title (str): movie title
        watched (bool): if the movie has been market as watched

    Methods:
        None

    Signals:
        None
    """

    __gtype_name__ = 'MovieModel'

    add_date = GObject.Property(type=str, default='')
    backdrop_path = GObject.Property(type=str, default='')
    budget = GObject.Property(type=float, default=0)
    genres = GObject.Property(type=GLib.strv_get_type())
    id = GObject.Property(type=str, default='')
    manual = GObject.Property(type=bool, default=False)
    original_language = GObject.Property(type=LanguageModel)
    original_title = GObject.Property(type=str, default='')
    overview = GObject.Property(type=str, default='')
    poster_path = GObject.Property(type=str, default='')
    release_date = GObject.Property(type=str, default='')
    revenue = GObject.Property(type=float, default=0)
    runtime = GObject.Property(type=int, default=0)
    status = GObject.Property(type=str, default='')
    tagline = GObject.Property(type=str, default='')
    title = GObject.Property(type=str, default='')
    watched = GObject.Property(type=bool, default=False)

    def __init__(self, d=None, t=None):
        super().__init__()

        if d is not None:
            self.add_date = datetime.now()
            self.backdrop_path = self._download_background(
                path=d['backdrop_path'])
            self.budget = d['budget']
            self.genres = self._parse_genres(api_dict=d['genres'])
            self.id = d['id']
            self.manual = False
            self.original_language = local.LocalProvider.get_language_by_code(
                d['original_language'])  # type: ignore
            self.original_title = d['original_title']
            self.overview = re.sub(r'\s{2}', ' ', d['overview'])
            self.poster_path = self._download_poster(path=d['poster_path'])
            self.release_date = d['release_date']
            self.revenue = d['revenue']
            self.runtime = d['runtime']
            self.status = d['status']
            self.tagline = d['tagline']
            self.title = d['title']
            self.watched = False
        else:
            self.add_date = t[0]  # type: ignore
            self.backdrop_path = t[1]  # type: ignore
            self.budget = t[2]  # type: ignore
            self.genres = self._parse_genres(db_str=t[3])  # type: ignore
            self.id = t[4]  # type: ignore
            self.manual = t[5]  # type:ignore
            self.original_language = local.LocalProvider.get_language_by_code(
                t[6])  # type: ignore
            self.original_title = t[7]  # type: ignore
            self.overview = t[8]  # type: ignore
            self.poster_path = t[9]  # type: ignore
            self.release_date = t[10]  # type: ignore
            self.revenue = t[11]  # type: ignore
            self.runtime = t[12]  # type: ignore
            self.status = t[13]  # type: ignore
            self.tagline = t[14]  # type: ignore
            self.title = t[15]  # type: ignore
            self.watched = t[16]  # type:ignore

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
        r = requests.get(url)
        if r.status_code == 200:
            with open(f'{shared.poster_dir}{path}', 'wb') as f:
                f.write(r.content)
            return f'file://{shared.poster_dir}{path}'

        return f'resource://{shared.PREFIX}/blank_poster.jpg'
