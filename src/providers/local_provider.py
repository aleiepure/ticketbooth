# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import sqlite3

from .. import shared  # type: ignore
from ..models.language_model import LanguageModel
from ..models.movie_model import MovieModel
from ..providers.tmdb_provider import TMDBProvider as tmdb


class LocalProvider:
    """
    This class provides methods to interface with the local db.

    Properties:
        None

    Methods:
        create_movies_table(): Creates the table used to store movie details in a local database
        create_series_table(): Creates the table used to store tv series details in a local database
        create_languages_table(): Creates the table used to store the available languages in a local database
        create_tables(): Convenience method to create all tables with a single call
        add_language(language: LanguageModel): Inserts the provided LanguageModel in the languages table
    """

    @staticmethod
    def create_movies_table() -> None:
        """
        Creates the table used to store movie details in a local database.

        Args:
            None

        Returns:
            None
        """

        with sqlite3.connect(shared.data_dir / 'data') as connection:
            sql = """CREATE TABLE IF NOT EXISTS movies (
                        backdrop_path TEXT,
                        budget INTEGER,
                        genres TEXT,
                        id INTEGER PRIMARY KEY,
                        original_language TEXT,
                        original_title TEXT,
                        overview TEXT,
                        poster_path TEXT,
                        release_date TEXT,
                        revenue INTEGER,
                        runtime INTEGER NOT NULL,
                        status TEXT,
                        tagline TEXT,
                        title TEXT NOT NULL,
                        FOREIGN KEY (original_language) REFERENCES languages (iso_639_1)
                     );"""
            connection.cursor().execute(sql)
            connection.commit()

    @staticmethod
    def create_series_table() -> None:
        """
        Creates the table used to store tv series details in a local database.
        Not implemented yet.

        Args:
            None

        Returns:
            None
        """

        pass

    @staticmethod
    def create_languages_table() -> None:
        """
        Creates the table used to store the available languages in a local database.
        Not implemented yet.

        Args:
            None

        Returns:
            None
        """

        with sqlite3.connect(shared.data_dir / 'data') as connection:
            sql = """CREATE TABLE IF NOT EXISTS languages (
                        iso_639_1 TEXT PRIMARY KEY,
                        name TEXT NOT NULL
                     );"""
            connection.cursor().execute(sql)
            connection.commit()

    @staticmethod
    def create_tables() -> None:
        """
        Convenience method to create all tables with a single call.

        Args:
            None

        Returns:
            None
        """

        LocalProvider.create_movies_table()
        LocalProvider.create_series_table()
        LocalProvider.create_languages_table()

    @staticmethod
    def add_language(language: LanguageModel) -> int | None:
        """
        Inserts the provided LanguageModel in the languages table.

        Args:
            language: a LanguageModel to insert

        Returns:
            lastrowid: int or None containing the id of the last inserted row
        """

        with sqlite3.connect(shared.data_dir / 'data') as connection:
            sql = 'INSERT INTO languages VALUES (?,?);'
            result = connection.cursor().execute(sql, (language.iso_name, language.name))
            connection.commit()
        return result.lastrowid

    @staticmethod
    def add_movie(tmdb_id: int) -> int | None:
        """
        Queries the information about the movie with the id provided and inserts it into the movie table.

        Args:
            tmdb_id (int): id of the content

        Returns:
            int or None containing the id of the last inserted row
        """

        movie = MovieModel(tmdb.get_movie(tmdb_id))
        with sqlite3.connect(shared.data_dir / 'data') as connection:
            sql = 'INSERT INTO movies VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?);'
            result = connection.cursor().execute(sql, (
                movie.backdrop_path,
                movie.budget,
                ','.join(movie.genres),
                movie.id,
                movie.original_language.iso_name,
                movie.original_title,
                movie.overview,
                movie.poster_path,
                movie.release_date,
                movie.revenue,
                movie.runtime,
                movie.status,
                movie.tagline,
                movie.title,
            ))
            connection.commit()
        return result.lastrowid

    @staticmethod
    def add_series(tmdb_id: int) -> int | None:
        """
        Queries the information about the tv series with the id provided and inserts it into the tv series table.

        Args:
            tmdb_id (int): id of the content

        Returns:
            int or None containing the id of the last inserted row
        """
        pass

    @staticmethod
    def add_content(tmdb_id: int, media_type: str) -> int | None:
        """
        Convenience method to add movies and series without using separate methods.

        Args:
            tmdb_id (int): id of the content
            media_type (str): content's media type

        Returns:
            int or None containing the id of the last inserted row
        """

        if media_type == 'movie':
            return LocalProvider.add_movie(tmdb_id=tmdb_id)
        else:
            return LocalProvider.add_series(tmdb_id=tmdb_id)

    @staticmethod
    def get_language_by_code(code: str) -> LanguageModel:
        with sqlite3.connect(shared.data_dir / 'data') as connection:
            sql = """SELECT * FROM languages WHERE iso_639_1 = ?"""
            result = connection.cursor().execute(sql, (code,)).fetchone()
            return LanguageModel(iso_name=result[0], name=result[1])
