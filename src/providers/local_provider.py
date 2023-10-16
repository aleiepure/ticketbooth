# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import os
import shutil
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
        add_movie(id: int, movie: MovieModel): Inserts a movie in the movies table, querying the data from TMDB if only
            id is provided.
        add_series(id: int, serie: SeriesModel): Inserts a tv series in the series table, querying the data from TMDB
            if only id is provided.
        add_content(id: int, media_type: str): Convenience method to add movies and series from TMDB without using
            separate methods
        get_language_by_code(iso_code: str): Retrieves a language from the db via its iso_639_1 code.
        get_movie_by_id(id: str): Retrieves a movie from the db via its id
        get_all_movies(): Retrieves all movies from the db
        mark_watched_movie(id: str, status: bool): Sets the watched flag on the movie with the provided id.
        delete_movie(id: str): Deletes the movie with the provided id, removing associated files too.
        get_all_seasons(show: str): Retrieves metadata for all seasons of a show.
        get_season_episodes(show: str, season_number: int): Retrieves the episodes for a season of a show
        get_series_by_id(id: str): Retrieves the series with the provided id.
        get_all_series(): Retrieves all tv series from the db.
        mark_watched_series(id: str, watched: bool): Sets the watched flag on all episodes in the series and the series
            itself.
        delete_series(id: str): Deletes the tv series with the provided id, removing associated files too.
        get_all_languages(): Retrieves all languages from the db.
        get_next_manual_movie(): Calculates the next id for a manually added movie.
        get_next_manual_series(): Calculates the next id for a manually added tv series.
        get_next_manual_season(): Calculates the next id for a manually added season.
        get_next_manual_episode(): Calculates the next id for a manually added episode.
        get_language_by_name(name: str): Retrieves a language from the db via its name.
        update_movie(old: MovieModel, new: MovieModel): Updates a movie with new data.
        mark_watched_episode(id: str, watched: bool): Sets the watched flag on the specified episode.
        get_episode_by_id(id: str): Retrieves an episode from the db via its id.
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
            logging.debug('[db] Create movie table')
            sql = """CREATE TABLE IF NOT EXISTS movies (
                        add_date TEXT,
                        backdrop_path TEXT,
                        budget INTEGER,
                        genres TEXT,
                        id TEXT PRIMARY KEY,
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
                        title TEXT,
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
            logging.debug('[db] Create series, seasons, and episodes tables')
            series_sql = """CREATE TABLE IF NOT EXISTS series (
                            add_date TEXT,
                            backdrop_path TEXT,
                            created_by TEXT,
                            episodes_number INT,
                            genres TEXT,
                            id TEXT PRIMARY KEY,
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
                            title TEXT,
                            watched BOOLEAN,
                            FOREIGN KEY (original_language) REFERENCES languages (iso_639_1)
                        );"""
            seasons_sql = """CREATE TABLE IF NOT EXISTS seasons (
                                episodes_number INTEGER,
                                id TEXT PRIMARY KEY,
                                number INTEGER,
                                overview TEXT,
                                poster_path TEXT,
                                title TEXT,
                                show_id INTERGER,
                                FOREIGN KEY (show_id) REFERENCES series (id) ON DELETE CASCADE
                            );"""
            episodes_sql = """CREATE TABLE IF NOT EXISTS episodes (
                                id TEXT PRIMARY KEY,
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
            logging.debug('[db] Create languages table')
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
            logging.debug(f'[db] Add {language.name}: {result.lastrowid}')
        return result.lastrowid

    @staticmethod
    def add_movie(id: int = 0, movie: MovieModel | None = None) -> int | None:
        """
        Inserts a movie in the movies table, querying the data from TMDB if only id is provided.

        Args:
            id (int): tmdb id to query
            movie (MovieModel or None): movie to add

        Returns:
            int or None containing the id of the last inserted row
        """

        if not movie:
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
            logging.debug(
                f'[db] Add {movie.title}, {movie.release_date}: {result.lastrowid}')
        return result.lastrowid

    @staticmethod
    def add_series(id: int = 0, serie: SeriesModel | None = None) -> int | None:
        """
        Inserts a tv series in the series table, querying the data from TMDB if only id is provided.

        Args:
            id (int): tmdb id to query
            serie (SeriesModel or None): tv series to add

        Returns:
            int or None containing the id of the last inserted row
        """

        if not serie:
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
            logging.debug(
                f'[db] Add {serie.title}, {serie.release_date}: {result.lastrowid}')
        return result.lastrowid

    @staticmethod
    def add_content(id: int, media_type: str) -> int | None:
        """
        Convenience method to add movies and series from TDMB without using separate methods.

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
                language = LanguageModel(t=result)
                logging.debug(
                    f'[db] Get language by code {iso_code}: {language.name}')
                return language
            else:
                logging.error(f'[db] Get language by code {iso_code}: {None}')
                return None

    @staticmethod
    def get_movie_by_id(id: str) -> MovieModel | None:
        """
        Retrieves a movie from the db via its id.

        Args:
            id (str): id of the movie to look for

        Returns:
            MovieModel of the requested movie or None if not found in db
        """

        with sqlite3.connect(shared.db) as connection:
            sql = """SELECT * FROM movies WHERE id = ?;"""
            result = connection.cursor().execute(sql, (id,)).fetchone()
            if result:
                movie = MovieModel(t=result)
                logging.debug(
                    f'[db] Get movie id {id}: {movie.title}, {movie.release_date}')
                return movie
            else:
                logging.error(f'[db] Get movie id {id}: None')
                return None

    @staticmethod
    def get_all_movies() -> List[MovieModel]:
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
                logging.debug(f'[db] Get all movies: {result}')
                movies = []
                for movie in result:
                    movies.append(MovieModel(t=movie))
                return movies
            else:
                logging.debug(f'[db] Get all movies: {[]}')
                return []

    @staticmethod
    def mark_watched_movie(id: str, watched: bool) -> int | None:
        """
        Sets the watched flag on the movie with the provided id.

        Args:
            id (str): movie id to change
            watched (bool): status to set the flag to

        Returns:
            int or None containing the id of the last modified row
        """

        with sqlite3.connect(shared.db) as connection:
            sql = """UPDATE movies SET watched = ? WHERE id = ?"""
            result = connection.cursor().execute(sql, (watched, id,))
            connection.commit()
            logging.debug(
                f'[db] Mark movie {id} watched {watched}: {result.lastrowid}')
        return result.lastrowid

    @staticmethod
    def delete_movie(id: str) -> int | None:
        """
        Deletes the movie with the provided id, removing associated files too.

        Args:
            id (str): movie id to delete

        Returns:
            int or None containing the id of the last modified row
        """

        logging.debug(f'[db] Movie {id}, delete requested')
        movie = LocalProvider.get_movie_by_id(id)

        if movie.backdrop_path.startswith('file'):  # type: ignore
            os.remove(movie.backdrop_path[7:])      # type: ignore
            logging.debug(f'[db] Movie {id}, deleted backdrop')

        if movie.poster_path.startswith('file'):    # type: ignore
            os.remove(movie.poster_path[7:])        # type: ignore
            logging.debug(f'[db] Movie {id}, deleted poster')

        with sqlite3.connect(shared.db) as connection:
            sql = """DELETE FROM movies WHERE id = ?"""
            result = connection.cursor().execute(sql, (id,))
            connection.commit()
            logging.debug(f'[db] Movie {id}, deleted: {result.lastrowid}')

        return result.lastrowid

    @staticmethod
    def get_all_seasons(show: str) -> List[SeasonModel]:
        """
        Retrieves metadata for all seasons of a show.

        Args:
            show (str): id of the show

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
                logging.debug(f'[db] Get all seasons: {results}')
                for result in results:
                    seasons.append(SeasonModel(t=result))
            else:
                logging.debug(f'[db] Get all seasons: {[]}')

            return seasons

    @staticmethod
    def get_season_episodes(show: str, season_num: int) -> List[EpisodeModel]:
        """
        Retrieves the episodes for a season of a show.

        Args:
            show (str): id of the show
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
                logging.debug(
                    f'[db] Get show {show} season {season_num}: {results}')
                for result in results:
                    episodes.append(EpisodeModel(t=result))
            else:
                logging.debug(
                    f'[db] Get show {show} season {season_num}: {[]}')

            return episodes

    @staticmethod
    def get_series_by_id(id: str) -> SeriesModel | None:
        """
        Retrieves the series with the provided id.

        Args:
            id (str): id of the series to retrieve

        Returns:
            SeriesModel for the requested series or None
        """

        with sqlite3.connect(shared.db) as connection:
            sql = 'SELECT * FROM series WHERE id=?;'
            result = connection.cursor().execute(sql, (id,)).fetchone()
            if result:
                serie = SeriesModel(t=result)
                logging.debug(
                    f'[db] Get tv serie id {id}: {serie.title}')
                return serie
            else:
                logging.error(f'[db] Get tv serie id {id}: None')
                return None

    @staticmethod
    def get_all_series() -> List[SeriesModel]:
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
                logging.debug(f'[db] Get all tv series: {result}')
                series = []
                for serie in result:
                    series.append(SeriesModel(t=serie))
                return series
            else:
                logging.debug(f'[db] Get all tv series: {[]}')
                return []

    @staticmethod
    def mark_watched_series(id: str, watched: bool) -> int | None:
        """
        Sets the watched flag on the specified series.

        Args:
            id (str): tv series id to change
            watched (bool): status to set the flag to

        Returns:
            int or None containing the id of the last modified row
        """

        with sqlite3.connect(shared.db) as connection:
            sql = 'UPDATE series SET watched = ? WHERE id = ?;'
            result = connection.cursor().execute(sql, (watched, id,))
            connection.commit()
            logging.debug(
                f'[db] Mark tv serie {id} watched {watched}: {result.lastrowid}')
        return result.lastrowid

    @staticmethod
    def delete_series(id: str) -> int | None:
        """
        Deletes the tv series with the provided id, removing associated files too.

        Args:
            id (str): tv series id to delete

        Returns:
            int or None containing the id of the last modified row
        """

        logging.debug(f'[db] TV series {id}, delete requested')
        series = LocalProvider.get_series_by_id(id)

        if series.backdrop_path.startswith('file'):   # type: ignore
            os.remove(series.backdrop_path[7:])       # type: ignore
            logging.debug(f'[db] TV series {id}, deleted backdrop')

        if series.poster_path.startswith('file'):     # type: ignore
            os.remove(series.poster_path[7:])         # type: ignore
            logging.debug(f'[db] TV series {id}, deleted poster')

        if (shared.series_dir/id).is_dir():
            shutil.rmtree(shared.series_dir / id)
            logging.debug(
                f'[db] TV series {id}, deleted folder {shared.series_dir / id}')

        with sqlite3.connect(shared.db) as connection:
            connection.cursor().execute('PRAGMA foreign_keys = ON;')

            sql = """DELETE FROM series WHERE id = ?"""
            result = connection.cursor().execute(sql, (id,))
            connection.commit()
            logging.debug(f'[db] TV series {id}, deleted: {result.lastrowid}')

        return result.lastrowid

    @staticmethod
    def get_all_languages() -> List[LanguageModel]:
        """
        Retrieves all languages from the db.

        Args:
            None

        Returns:
            List of LanguageModel
        """
        with sqlite3.connect(shared.db) as connection:
            sql = 'SELECT * FROM languages ORDER BY iso_639_1'
            result = connection.cursor().execute(sql).fetchall()
            languages = []
            for language in result:
                languages.append(LanguageModel(t=language))
            logging.debug(f'[db] Get all languages: {result}')
            return languages

    @staticmethod
    def get_next_manual_movie() -> str:
        """
        Calculates the next id for a manually added movie.

        Args:
            None

        Returns:
            string with calculated id
        """

        with sqlite3.connect(shared.db) as connection:
            sql = "SELECT id FROM movies WHERE id LIKE 'M-%' ORDER BY id DESC;"
            result = connection.cursor().execute(sql).fetchone()
            if result:
                l = result[0].split('-')
                return f'{l[0]}-{int(l[1])+1}'
            else:
                return 'M-1'

    @staticmethod
    def get_next_manual_series() -> str:
        """
        Calculates the next id for a manually added tv series.

        Args:
            None

        Returns:
            string with calculated id
        """

        with sqlite3.connect(shared.db) as connection:
            sql = "SELECT id FROM series WHERE id LIKE 'M-%' ORDER BY id DESC;"
            result = connection.cursor().execute(sql).fetchone()
            if result:
                l = result[0].split('-')
                return f'{l[0]}-{int(l[1])+1}'
            else:
                return 'M-1'

    @staticmethod
    def get_next_manual_season() -> str:
        """
        Calculates the next id for a manually added season.

        Args:
            None

        Returns:
            string with calculated id
        """

        with sqlite3.connect(shared.db) as connection:
            sql = "SELECT id FROM seasons WHERE id LIKE 'M-%' ORDER BY id DESC;"
            result = connection.cursor().execute(sql).fetchone()
            if result:
                l = result[0].split('-')
                return f'{l[0]}-{int(l[1])+1}'
            else:
                return 'M-1'

    @staticmethod
    def get_next_manual_episode() -> str:
        """
        Calculates the next id for a manually added episode.

        Args:
            None

        Returns:
            string with calculated id
        """

        with sqlite3.connect(shared.db) as connection:
            sql = "SELECT id FROM episodes WHERE id LIKE 'M-%' ORDER BY id DESC;"
            result = connection.cursor().execute(sql).fetchone()
            if result:
                l = result[0].split('-')
                return f'{l[0]}-{int(l[1])+1}'
            else:
                return 'M-1'

    @staticmethod
    def get_language_by_name(name: str) -> LanguageModel | None:
        """
        Retrieves a language from the db via its name.

        Args:
            name (str):

        Returns:
            LanguageModel of the requested language or None if not found in db
        """

        with sqlite3.connect(shared.db) as connection:
            sql = 'SELECT * FROM languages WHERE name = ?;'
            result = connection.cursor().execute(sql, (name,)).fetchone()
            if result:
                language = LanguageModel(t=result)
                logging.debug(
                    f'[db] Get language by name {name}: {language.iso_name}')
                return language
            else:
                logging.error(f'[db] Get language by name {name}: {None}')
                return None

    @staticmethod
    def update_movie(old: MovieModel, new: MovieModel) -> int | None:
        """
        Updates a movie with new data.

        Args:
            old: movie to be updated
            new: new movie data

        Returns:
            int or None containing the id of the last modified row
        """

        with sqlite3.connect(shared.db) as connection:
            sql = """UPDATE movies
                     SET 
                         backdrop_path = ?,
                         budget = ?,
                         genres = ?,
                         manual = ?,
                         original_language = ?,
                         original_title = ?,
                         overview = ?,
                         poster_path = ?,
                         release_date = ?,
                         revenue = ?,
                         runtime = ?,
                         status = ?,
                         tagline = ?,
                         title = ?
                     WHERE id = ?;
                  """
            result = connection.cursor().execute(sql, (
                new.backdrop_path,
                new.budget,
                ','.join(new.genres),
                new.manual,
                new.original_language.iso_name,  # type: ignore
                new.original_title,
                new.overview,
                new.poster_path,
                new.release_date,
                new.revenue,
                new.runtime,
                new.status,
                new.tagline,
                new.title,
                old.id,
            ))
            connection.commit()
            logging.debug(f'[db] Update movie {old.id}: {(new.backdrop_path, new.budget, ",".join(new.genres), new.manual, new.original_language.iso_name, new.original_title, new.overview, new.poster_path, new.release_date, new.revenue, new.runtime, new.status, new.tagline, new.title, old.id)}')
        return result.lastrowid
    
    @staticmethod
    def mark_watched_episode(id: str, watched: bool) -> int | None:
        """
        Sets the watched flag on the specified episode.

        Args:
            id (str): episode id to change
            watched (bool): status to set the flag to

        Returns:
            int or None containing the id of the last modified row
        """
        with sqlite3.connect(shared.db, check_same_thread=False) as connection:
            sql = """UPDATE episodes SET watched = ? WHERE id = ?"""
            result = connection.cursor().execute(sql, (watched, id,))
            connection.commit()
            logging.debug(
                f'[db] Mark episode {id} watched {watched}: {result.lastrowid}')
        return result.lastrowid

    @staticmethod
    def get_episode_by_id(id: str) -> EpisodeModel | None:
        """
        Retrieves an episode from the db via its id.

        Args:
            id (str): id of the movie to look for

        Returns:
            EpisodeModel of the requested episode or None if not found in db
        """

        with sqlite3.connect(shared.db) as connection:
            sql = """SELECT * FROM episodes WHERE id = ?;"""
            result = connection.cursor().execute(sql, (id,)).fetchone()
            if result:
                episode = EpisodeModel(t=result)
                logging.debug(f'[db] Get episode id {id}: {episode.title}')
                return episode
            else:
                logging.error(f'[db] Get episode id {id}: None')
                return None
