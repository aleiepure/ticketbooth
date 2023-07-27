# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import glob
from typing import List

import requests
from gi.repository import GLib, GObject

import src.providers.local_provider as local

from .. import shared  # type: ignore
from ..models.language_model import LanguageModel


class MovieModel(GObject.GObject):
    """
    This class rappresents a movie object stored in the db.

    Properties:
        backdrop_path (str): path where the background image is stored
        budget (int): movie budget
        genres ([str]): list of genres
        id (int): movie id
        original_language (str): iso_639_1 code for the original language
        original_title (str): movie title in original language
        overview (str): movie overview, usually the main plot
        poster_path (str): path where the backgroud poster is stored
        release_date (str): release date in YYYY-MM-DD format
        revenue (int): movie revenue
        runtime (int): movie runtime in minutes
        tagline (str): movie tagline
        status (str): movie status, usually released or planned
        title (str): movie title

    Methods:
        None

    Signals:
        None
    """

    __gtype_name__ = 'MovieModel'

    backdrop_path = GObject.Property(type=str, default='')
    budget = GObject.Property(type=int, default=0)
    genres = GObject.Property(type=GLib.strv_get_type())
    id = GObject.Property(type=int, default=0)
    original_language = GObject.Property(type=LanguageModel)
    original_title = GObject.Property(type=str, default='')
    overview = GObject.Property(type=str, default='')
    poster_path = GObject.Property(type=str, default='')
    release_date = GObject.Property(type=str, default='')
    revenue = GObject.Property(type=int, default=0)
    runtime = GObject.Property(type=int, default=0)
    status = GObject.Property(type=str, default='')
    tagline = GObject.Property(type=str, default='')
    title = GObject.Property(type=str, default='')

    def __init__(self,
                 d=None,
                 backdrop_path: str = '',
                 budget: int = 0,
                 genres: str = '',
                 id: int = 0,
                 original_language: LanguageModel = LanguageModel(iso_name='xx', name='No Language'),
                 original_title: str = '',
                 overview: str = '',
                 poster_path: str = '',
                 release_date: str = '',
                 revenue: int = 0,
                 runtime: int = 0,
                 status: str = '',
                 tagline: str = '',
                 title: str = ''
                 ):
        super().__init__()

        if d is not None:
            self.backdrop_path = self._download_image(image_type='background', path=d['backdrop_path'])
            self.budget = d['budget']
            self.genres = self._parse_genres(api_dict=d['genres'])
            self.id = d['id']
            self.original_language = local.LocalProvider.get_language_by_code(d['original_language'])  # type: ignore
            self.original_title = d['original_title']
            self.overview = d['overview']
            self.poster_path = self._download_image(image_type='poster', path=d['poster_path'])
            self.release_date = d['release_date']
            self.revenue = d['revenue']
            self.runtime = d['runtime']
            self.status = d['status']
            self.tagline = d['tagline']
            self.title = d['title']
        else:
            self.backdrop_path = backdrop_path
            self.budget = budget
            self.genres = self._parse_genres(db_str=genres)
            self.id = id
            self.original_language = local.LocalProvider.get_language_by_code(original_language)  # type: ignore
            self.original_title = original_title
            self.overview = overview
            self.poster_path = poster_path
            self.release_date = release_date
            self.revenue = revenue
            self.runtime = runtime
            self.status = status
            self.tagline = tagline
            self.title = title

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

    def _download_image(self, image_type: str, path: str) -> str:
        """
        Returns the path of the image on the local filesystem, downloading if necessary.

        Args:
            image_type (str): image type, determines where it is stored
            path (str): path to dowload from

        Returns:
            str with the path of the image
        """

        if image_type == 'poster':
            directory = shared.poster_dir
        else:
            directory = shared.background_dir

        files = glob.glob(f'{path[1:-4]}.jpg', root_dir=directory)
        if files:
            return f'{directory}/{files[0]}'

        url = f'https://image.tmdb.org/t/p/w500{path}'
        r = requests.get(url)
        if r.status_code == 200:
            with open(f'{directory}{path}', 'wb') as f:
                f.write(r.content)
        return f'{directory}{path}'
