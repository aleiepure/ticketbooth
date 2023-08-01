# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import sqlite3
from typing import List

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

        with sqlite3.connect(shared.db) as connection:
            sql = """CREATE TABLE IF NOT EXISTS movies (
                        add_date TEXT,
                        backdrop_path TEXT,
                        budget INTEGER,
                        genres TEXT,
                        id INTEGER PRIMARY KEY,
                        manual BOOLEAN,
                        original_language TEXT,
                        original_title TEXT,
                        overview TEXT,
                        poster_path TEXT,
                        release_date TEXT,
                        revenue INTEGER,
                        runtime INTEGER,
                        status TEXT,
                        tagline TEXT,
                        title TEXT NOT NULL,
                        watched BOOLEAN,
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

        with sqlite3.connect(shared.db) as connection:
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

        with sqlite3.connect(shared.db) as connection:
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
        with sqlite3.connect(shared.db) as connection:
            sql = 'INSERT INTO movies VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);'
            result = connection.cursor().execute(sql, (
                movie.add_date,
                movie.backdrop_path,
                movie.budget,
                ','.join(movie.genres),
                movie.id,
                movie.manual,
                movie.original_language.iso_name,  # type: ignore
                movie.original_title,
                movie.overview,
                movie.poster_path,
                movie.release_date,
                movie.revenue,
                movie.runtime,
                movie.status,
                movie.tagline,
                movie.title,
                movie.watched,
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
    def get_language_by_code(iso_code: str) -> LanguageModel | None:
        """
        Retrieves a language from the db via its iso_639_1 code.

        Args:
            iso_code (str): iso_639_1 code of the language to look for

        Returns:
            LanguageModel of the requested language or None if not found in db
        """

        with sqlite3.connect(shared.db) as connection:
            sql = """SELECT * FROM languages WHERE iso_639_1 = ?"""
            result = connection.cursor().execute(sql, (iso_code,)).fetchone()
            if result:
                return LanguageModel(t=result)
            else:
                return None

    @staticmethod
    def get_movie_by_id(id: int) -> MovieModel | None:
        """
        Retrieves a movie from the db via its id.

        Args:
            id (int): id of the movie to look for

        Returns:
            MovieModel of the requested movie or None if not found in db
        """

        with sqlite3.connect(shared.db) as connection:
            sql = """SELECT * FROM movies WHERE id = ?;"""
            result = connection.cursor().execute(sql, (id,)).fetchone()
            if result:
                return MovieModel(t=result)
            else:
                return None

    @staticmethod
    def get_all_movies() -> List[MovieModel] | None:
        """
        Retrieves all movies from the db.

        Args:
            None

        Returns:
            List of MovieModel or None
        """

        with sqlite3.connect(shared.db) as connection:
            sql = """SELECT * FROM movies;"""
            result = connection.cursor().execute(sql).fetchall()
            if result:
                movies = []
                for movie in result:
                    movies.append(MovieModel(t=movie))
                return movies
            else:
                return None

    @staticmethod
    def mark_watched_movie(id: int, watched: bool) -> int | None:
        """
        Sets the watched flag on the movie with the provided id.

        Args:
            id (int): movie id to change
            watched (bool): status to set the flag to

        Returns:
            int or None containing the id of the last modified row
        """

        with sqlite3.connect(shared.db) as connection:
            sql = """UPDATE movies SET watched = ? WHERE id = ?"""
            result = connection.cursor().execute(sql, (watched, id,))
            connection.commit()
        return result.lastrowid

    @staticmethod
    def delete_movie(id: int) -> int | None:
        """
        Deletes the movie with the provided id.

        Args:
            id (int): movie id to delete

        Returns:
            int or None containing the id of the last modified row
        """

        with sqlite3.connect(shared.db) as connection:
            sql = """DELETE FROM movies WHERE id = ?"""
            result = connection.cursor().execute(sql, (id,))
            connection.commit()
        return result.lastrowid
