# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import glob
import re
from datetime import datetime
from typing import List
from pathlib import Path

import requests
from gi.repository import GLib, GObject
from PIL import Image, ImageFilter, ImageStat

import src.providers.local_provider as local

from .. import shared  # type: ignore
from ..models.language_model import LanguageModel


class MovieModel(GObject.GObject):
    """
    This class represents a movie object stored in the db.

    Properties:
        add_date (str): date of addition to the db (ISO format)
        backdrop_path (str): path where the background image is stored
        budget (float): movie budget
        color (bool): color of the poster badges, False being dark
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
    color = GObject.Property(type=bool, default=False)
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
            self.poster_path,self.color = self._download_poster(path=d['poster_path'], color = False)
            self.release_date = d['release_date']
            self.revenue = d['revenue']
            self.runtime = d['runtime']
            self.status = d['status']
            self.tagline = d['tagline']
            self.title = d['title']
            self.watched = False
        else:
            self.add_date = t["add_date"]  # type: ignore
            self.backdrop_path = t["backdrop_path"]  # type: ignore
            self.budget = t["budget"]  # type: ignore
            self.color = t["color"]
            self.genres = self._parse_genres(db_str=t["genres"])  # type: ignore
            self.id = t["id"]  # type: ignore
            self.manual = t["manual"]  # type:ignore
            self.original_language = local.LocalProvider.get_language_by_code(
                t["original_language"])  # type: ignore
            self.original_title = t["original_title"]  # type: ignore
            self.overview = t["overview"]  # type: ignore
            self.poster_path = t["poster_path"]  # type: ignore
            self.release_date = t["release_date"]  # type: ignore
            self.revenue = t["revenue"]  # type: ignore
            self.runtime = t["runtime"]  # type: ignore
            self.status = t["status"]  # type: ignore
            self.tagline = t["tagline"]  # type: ignore
            self.title = t["title"]  # type: ignore
            self.watched = t["watched"]  # type:ignore

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

    def _download_poster(self, path: str, color: bool) -> (str,bool):
        """
        Returns the uri of the poster image on the local filesystem, downloading if necessary.

        Args:
            path (str): path to dowload from

        Returns:
            str with the uri of the poster image
        """

        if not path:
            return (f'resource://{shared.PREFIX}/blank_poster.jpg', False)

        files = glob.glob(f'{path[1:-4]}.jpg', root_dir=shared.poster_dir)
        if files:
            color = self._compute_badge_color(Path(f'{files[0]}'))
            return (f'file://{shared.poster_dir}/{files[0]}',color)

        url = f'https://image.tmdb.org/t/p/w500{path}'
        try:
            r = requests.get(url)
            if r.status_code == 200:
                with open(f'{shared.poster_dir}{path}', 'wb') as f:
                    f.write(r.content)
                color = self._compute_badge_color(Path(f'{path}'))
                return (f'file://{shared.poster_dir}{path}', color)
            else:
                return f'resource://{shared.PREFIX}/blank_poster.jpg'
        except (requests.exceptions.ConnectionError, requests.exceptions.SSLError):
            return f'resource://{shared.PREFIX}/blank_poster.jpg'

    def _compute_badge_color(self, path: str) -> bool:
        color_light = False
        im = Image.open(Path(f'{shared.poster_dir}/{path}'))
        box = (im.size[0]-175, 0, im.size[0], 175)
        region = im.crop(box)
        median = ImageStat.Stat(region).median
        if sum(median) < 3 * 128:
            color_light = True

        return color_light
