# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import glob
import os
import re

import requests
from gi.repository import GObject
from PIL import Image

from .. import shared  # type: ignore


class EpisodeModel(GObject.GObject):
    """
    This class represents an episode object stored in the db.

    Properties:
        id (str): episode id
        number (int): episode number in its season
        overview (str): episode overview
        runtime (int): episode runtime in minutes
        season_number (int): season the episode belongs to
        show_id (int): id of the show the episode belongs to
        still_path (str): uri of the episode still
        title (str): episode title
        watched (bool): whether the episode has been watched or not

    Methods:
        None

    Signals:
        None
    """

    __gtype_name__ = 'EpisodeModel'

    id = GObject.Property(type=str, default='')
    number = GObject.Property(type=int, default=0)
    overview = GObject.Property(type=str, default='')
    runtime = GObject.Property(type=int, default=0)
    season_number = GObject.Property(type=int, default=0)
    show_id = GObject.Property(type=str, default='')
    still_path = GObject.Property(type=str, default='')
    title = GObject.Property(type=str, default='')
    watched = GObject.Property(type=bool, default=False)

    def __init__(self, d=None, t=None):
        super().__init__()

        if d is not None:
            self.id = d['id']
            self.number = d['episode_number']
            self.overview = re.sub(r'\s{2}', ' ', d['overview'])
            self.runtime = d['runtime'] if d['runtime'] else 0
            self.season_number = d['season_number']
            self.show_id = d['show_id']
            self.still_path = self._download_still(d['still_path'])
            self.title = d['name']
            self.watched = False
        else:
            self.id = t[0]  # type: ignore
            self.number = t[1]  # type: ignore
            self.overview = t[2]  # type: ignore
            self.runtime = t[3]  # type: ignore
            self.season_number = t[4]  # type: ignore
            self.show_id = t[5]  # type: ignore
            self.still_path = t[6]  # type: ignore
            self.title = t[7]  # type: ignore
            self.watched = t[8]  # type: ignore

    def _download_still(self, path: str) -> str:
        """
        Returns the uri of the still image on the local filesystem, downloading if necessary.

        Args:
            path (str): path to dowload from

        Returns:
            str with the uri of the still image
        """

        if not path:
            return f'resource://{shared.PREFIX}/blank_still.jpg'

        if not os.path.exists(f'{shared.series_dir}/{self.show_id}/{self.season_number}'):
            os.makedirs(
                f'{shared.series_dir}/{self.show_id}/{self.season_number}')

        files = glob.glob(
            f'{path[1:-4]}.jpg', root_dir=f'{shared.series_dir}/{self.show_id}/{self.season_number}')
        if files:
            return f'file://{shared.series_dir}/{self.show_id}/{self.season_number}/{files[0]}'

        url = f'https://image.tmdb.org/t/p/w500{path}'
        try:
            r = requests.get(url)
            if r.status_code == 200:
                with open(f'{shared.series_dir}/{self.show_id}/{self.season_number}{path}', 'wb') as f:
                    f.write(r.content)

                with Image.open(f'{shared.series_dir}/{self.show_id}/{self.season_number}{path}') as img:
                    img = img.resize((500, 281))
                    img.save(
                        f'{shared.series_dir}/{self.show_id}/{self.season_number}{path}', 'JPEG')
                return f'file://{shared.series_dir}/{self.show_id}/{self.season_number}{path}'
            else:
                return f'resource://{shared.PREFIX}/blank_still.jpg'
        except (requests.exceptions.ConnectionError, requests.exceptions.SSLError):
            return f'resource://{shared.PREFIX}/blank_still.jpg'
