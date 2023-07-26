# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import sqlite3

from .. import shared  # type: ignore
from ..models.language_model import LanguageModel


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
                        tagline TEXT,
                        status TEXT,
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
            lastrowid: int or None containing the id of the last inserted row.
        """

        with sqlite3.connect(shared.data_dir / 'data') as connection:
            sql = 'INSERT INTO languages (iso_639_1, name) VALUES(?,?)'
            result = connection.cursor().execute(sql, (language.iso_name, language.name))
            connection.commit()
        return result.lastrowid
