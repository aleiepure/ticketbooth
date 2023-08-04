# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import glob
import os
import re
from typing import List

import requests
from gi.repository import GObject

import src.providers.local_provider as local
import src.providers.tmdb_provider as tmdb
from src.models.episode_model import EpisodeModel

from .. import shared  # type: ignore
from ..models.language_model import LanguageModel


class SeasonModel(GObject.GObject):
    """
    This class rappresents a season object stored in the db.

    Properties:
        episodes (List[EpisodeModel]): list of episodes in self
        episodes_number (int): number of episodes in self
        id (int): season id
        number (int): season number
        overview (str): season overview
        poster_path (str): uri of the season's poster
        show_id (int):  id of the show the searies belongs to
        title (str): season title

    Methods:
        None

    Signals:
        None
    """

    __gtype_name__ = 'SeasonModel'

    episodes = GObject.Property(type=object)
    episodes_number = GObject.Property(type=int, default=0)
    id = GObject.Property(type=int, default=0)
    number = GObject.Property(type=int, default=0)
    overview = GObject.Property(type=str, default='')
    poster_path = GObject.Property(type=str, default='')
    show_id = GObject.Property(type=int, default=0)
    title = GObject.Property(type=str, default='')

    def __init__(self, show_id: int = 0, d=None, t=None):
        super().__init__()

        if d is not None:
            self.episodes_number = d['episode_count']
            self.id = d['id']
            self.number = d['season_number']
            self.overview = re.sub(r'\s{2}', ' ', d['overview'])
            self.poster_path = self._download_poster(show_id, d['poster_path'])
            self.title = d['name']
            self.show_id = show_id

            self.episodes = self._parse_episodes(tmdb.TMDBProvider.get_season_episodes(show_id, self.number))
        else:
            self.episodes_number = t[0]  # type:ignore
            self.id = t[1]  # type:ignore
            self.number = t[2]  # type:ignore
            self.overview = t[3]  # type:ignore
            self.poster_path = t[4]  # type:ignore
            self.title = t[5]  # type:ignore
            self.show_id = t[6]  # type:ignore

            self.episodes = local.LocalProvider.get_season_episodes(self.show_id, self.number)  # type: ignore

    def _download_poster(self, show_id: int, path: str) -> str:
        """
        Returns the uri of the poster image on the local filesystem, downloading if necessary.

        Args:
            path (str): path to dowload from

        Returns:
            str with the uri of the poster image
        """

        if not path:
            return f'resource://{shared.PREFIX}/blank_poster.jpg'

        if not os.path.exists(f'{shared.series_dir}/{show_id}/{self.number}'):
            os.makedirs(f'{shared.series_dir}/{show_id}/{self.number}')

        files = glob.glob(f'{path[1:-4]}.jpg', root_dir=f'{shared.series_dir}/{show_id}/{self.number}')
        if files:
            return f'file://{shared.series_dir}/{show_id}/{self.number}/{files[0]}'

        url = f'https://image.tmdb.org/t/p/w500{path}'
        r = requests.get(url)
        if r.status_code == 200:
            with open(f'{shared.series_dir}/{show_id}/{self.number}{path}', 'wb') as f:
                f.write(r.content)
            return f'file://{shared.series_dir}/{show_id}/{self.number}{path}'

        return f'resource://{shared.PREFIX}/blank_poster.jpg'

    def _parse_episodes(self, episodes: dict) -> List[EpisodeModel]:
        """
        Parses episode data comming from tmdb into a list of EpisodeModels.

        Args:
            episodes (dict): dict from the api

        Returns:
            List of EpisodeModels
        """

        episode_list = []

        for episode in episodes:
            episode_list.append(EpisodeModel(d=episode))
        return episode_list
