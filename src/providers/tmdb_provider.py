# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os

import tmdbsimple as tmdb
from gi.repository import Gdk, Gio

from .. import shared  # type: ignore


class TMDBProvider:

    tmdb.API_KEY = os.environ.get('TMDB_KEY')

    @staticmethod
    def search(query: str, lang: str = shared.schema.get_string('tmdb-lang')) -> dict:
        return tmdb.Search().multi(query=query, language=lang)
