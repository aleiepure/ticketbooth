# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import sqlite3
from typing import List

from .. import shared  # type: ignore
from ..models.episode_model import EpisodeModel
from ..models.language_model import LanguageModel
from ..models.movie_model import MovieModel
from ..models.season_model import SeasonModel
from ..models.series_model import SeriesModel
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
        add_movie(id: int): Queries the movie and inserts it into the db
        add_series(id: int): Queries the series and inserts it into the db
        add_content(id: int, media_type: str): Convenience method to add movies and series without using separate methods
        get_language_by_code(iso_code: str): Retrieves a language from the db
        get_movie_by_id(id: int): Retrieves a movie from the db via its id
        get_all_movies(): Retrieves all movies from the db
        mark_watched_movie(id: int, status: bool): Sets the watched flag on a movie
        delete_movie(id: int): Deletes a movie
        get_all_seasons(show: int): Retrieves all seasons of a show
        get_season_episodes(show: int, season_number: int): Retrieves the episodes for a season of a show
        get_series_by_id(id: int): Retrieves a series from the db via its id
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

        Args:
            None

        Returns:
            None
        """

        with sqlite3.connect(shared.db) as connection:
            series_sql = """CREATE TABLE IF NOT EXISTS series (
                            add_date TEXT,
                            backdrop_path TEXT,
                            created_by TEXT,
                            episodes_number INT,
                            genres TEXT,
                            id INTEGER PRIMARY KEY,
                            in_production BOOLEAN,
                            manual BOOLEAN,
                            original_language TEXT,
                            original_title TEXT,
                            overview TEXT,
                            poster_path TEXT,
                            release_date TEXT,
                            seasons_number INT,
                            status TEXT,
                            tagline TEXT,
                            title TEXT NOT NULL,
                            watched BOOLEAN,
                            FOREIGN KEY (original_language) REFERENCES languages (iso_639_1)
                        );"""
            seasons_sql = """CREATE TABLE IF NOT EXISTS seasons (
                                episodes_number INTEGER,
                                id INTEGER PRIMARY KEY,
                                number INTEGER,
                                overview TEXT,
                                poster_path TEXT,
                                title TEXT,
                                show_id INTERGER,
                                FOREIGN KEY (show_id) REFERENCES series (id) ON DELETE CASCADE
                            );"""
            episodes_sql = """CREATE TABLE IF NOT EXISTS episodes (
                                id INTEGER PRIMARY KEY,
                                number INTEGER,
                                overview TEXT,
                                runtime INTEGER,
                                season_number INTEGER,
                                show_id INTEGER,
                                still_path TEXT,
                                title TEXT,
                                watched BOOLEAN,
                                FOREIGN KEY (show_id) REFERENCES series (id) ON DELETE CASCADE
                            );"""
            connection.cursor().execute(series_sql)
            connection.cursor().execute(seasons_sql)
            connection.cursor().execute(episodes_sql)
            connection.commit()

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
    def add_movie(id: int) -> int | None:
        """
        Queries the information about the movie with the id provided and inserts it into the movie table.

        Args:
            id (int): id of the content

        Returns:
            int or None containing the id of the last inserted row
        """

        movie = MovieModel(tmdb.get_movie(id))
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
    def add_series(id: int) -> int | None:
        """
        Queries the information about the tv series with the id provided and inserts it into the tv series table.

        Args:
            id (int): id of the content

        Returns:
            int or None containing the id of the last inserted row
        """

        serie = SeriesModel(tmdb.get_serie(id))
        with sqlite3.connect(shared.db) as connection:
            sql = 'INSERT INTO series VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);'
            result = connection.cursor().execute(sql, (
                serie.add_date,
                serie.backdrop_path,
                ','.join(serie.created_by),
                serie.episodes_number,
                ','.join(serie.genres),
                serie.id,
                serie.in_production,
                serie.manual,
                serie.original_language.iso_name,  # type: ignore
                serie.original_title,
                serie.overview,
                serie.poster_path,
                serie.release_date,
                serie.seasons_number,
                serie.status,
                serie.tagline,
                serie.title,
                serie.watched,
            ))

            for season in serie.seasons:
                sql = 'INSERT INTO seasons VALUES (?,?,?,?,?,?,?);'
                connection.cursor().execute(sql, (
                    season.episodes_number,
                    season.id,
                    season.number,
                    season.overview,
                    season.poster_path,
                    season.title,
                    season.show_id
                ))

                for episode in season.episodes:
                    sql = 'INSERT INTO episodes VALUES (?,?,?,?,?,?,?,?,?);'
                    connection.cursor().execute(sql, (
                        episode.id,
                        episode.number,
                        episode.overview,
                        episode.runtime,
                        episode.season_number,
                        episode.show_id,
                        episode.still_path,
                        episode.title,
                        episode.watched
                    ))

            connection.commit()
        return result.lastrowid

    @staticmethod
    def add_content(id: int, media_type: str) -> int | None:
        """
        Convenience method to add movies and series without using separate methods.

        Args:
            id (int): id of the content
            media_type (str): content's media type

        Returns:
            int or None containing the id of the last inserted row
        """

        if media_type == 'movie':
            return LocalProvider.add_movie(id)
        else:
            return LocalProvider.add_series(id)

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

    @staticmethod
    def get_all_seasons(show: int) -> List[SeasonModel]:
        """
        Retrieves metadata for all seasons of a show.

        Args:
            show (int): id of the show

        Returns:
            list of SeasonModel
        """

        seasons = []

        with sqlite3.connect(shared.db) as connection:
            sql = """SELECT *
                     FROM seasons
                     WHERE show_id = ?
                     ORDER BY number;"""

            results = connection.cursor().execute(sql, (show,)).fetchall()
            if results:
                for result in results:
                    seasons.append(SeasonModel(t=result))

            return seasons

    @staticmethod
    def get_season_episodes(show: int, season_num: int) -> List[EpisodeModel]:
        """
        Retrieves the episodes for a season of a show.

        Args:
            show (int): id of the show
            season_num (int): season number

        Returns:
            list of EpisodeModel
        """

        episodes = []

        with sqlite3.connect(shared.db) as connection:
            sql = """SELECT *
                     FROM episodes
                     WHERE show_id = ? AND
                           season_number = ?
                     ORDER BY number;"""

            results = connection.cursor().execute(sql, (show, season_num,)).fetchall()
            if results:
                for result in results:
                    episodes.append(EpisodeModel(t=result))

            return episodes

    @staticmethod
    def get_series_by_id(id: int) -> SeriesModel | None:
        """
        Retrieves the series with the provided id.

        Args:
            id (int): id of the series to retrieve

        Returns:
            SeriesModel for the requested series or None
        """

        with sqlite3.connect(shared.db) as connection:
            sql = 'SELECT * FROM series WHERE id=?;'
            result = connection.cursor().execute(sql, (id,)).fetchone()
            if result:
                return SeriesModel(t=result)
            else:
                return None

    @staticmethod
    def get_all_series() -> List[SeriesModel] | None:
        """
        Retrieves all tv series from the db.

        Args:
            None

        Returns:
            List of SeriesModel or None
        """

        with sqlite3.connect(shared.db) as connection:
            sql = """SELECT * FROM series;"""
            result = connection.cursor().execute(sql).fetchall()
            if result:
                series = []
                for serie in result:
                    series.append(SeriesModel(t=serie))
                return series
            else:
                return None

    @staticmethod
    def mark_watched_series(id: int, watched: bool) -> int | None:
        """
        Sets the watched flag on all episodes in the series and the series itself.

        Args:
            id (int): tv series id to change
            watched (bool): status to set the flag to

        Returns:
            int or None containing the id of the last modified row
        """

        with sqlite3.connect(shared.db) as connection:
            sql = """UPDATE episodes SET watched = ? WHERE show_id = ?"""
            connection.cursor().execute(sql, (watched, id,))
            sql = 'UPDATE series SET watched = ? WHERE id = ?;'
            result = connection.cursor().execute(sql, (watched, id,))
            connection.commit()
        return result.lastrowid

    @staticmethod
    def delete_series(id: int) -> int | None:
        """
        Deletes the tv series with the provided id.

        Args:
            id (int): tv series id to delete

        Returns:
            int or None containing the id of the last modified row
        """

        with sqlite3.connect(shared.db) as connection:
            connection.cursor().execute('PRAGMA foreign_keys = ON;')

            sql = """DELETE FROM series WHERE id = ?"""
            result = connection.cursor().execute(sql, (id,))
            connection.commit()
        return result.lastrowid
