# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import shutil
from datetime import date, datetime
from gettext import gettext as _
from typing import List
from urllib.parse import unquote

from gi.repository import Adw, GLib, GObject, Gtk

from .. import shared  # type: ignore
from ..background_queue import (ActivityType, BackgroundActivity,
                                BackgroundQueue)
from ..dialogs.edit_season_dialog import EditSeasonDialog
from ..models.episode_model import EpisodeModel
from ..models.language_model import LanguageModel
from ..models.movie_model import MovieModel
from ..models.season_model import SeasonModel
from ..models.series_model import SeriesModel
from ..providers.local_provider import LocalProvider as local
from ..widgets.season_expander import SeasonExpander


@Gtk.Template(resource_path=shared.PREFIX + '/ui/dialogs/add_manual.ui')
class AddManualDialog(Adw.Window):
    """
    This class rappresents the window to manually add content to the db.

    Properties:
        edit_mode (bool): whether or not the window is in add/edit mode

    Methods:
        update_seasons_ui(): rebuilds the ui to reflect changes to seasons
        get_season(title: str, poster: str, episodes: list): returns the tuple with the provided data or an empty tuple

    Signals:
        edit-saved(SeriesModel or MovieMovel): emited when the user clicks the save button
    """

    __gtype_name__ = 'AddManualDialog'

    edit_mode = GObject.Property(type=bool, default=False)

    _movies_btn = Gtk.Template.Child()
    _series_btn = Gtk.Template.Child()
    _save_btn = Gtk.Template.Child()
    _poster = Gtk.Template.Child()
    _title_entry = Gtk.Template.Child()
    _release_date_menu_btn = Gtk.Template.Child()
    _calendar = Gtk.Template.Child()
    _genres_entry = Gtk.Template.Child()
    _runtime_spinrow = Gtk.Template.Child()
    _tagline_entry = Gtk.Template.Child()
    _creator_entry = Gtk.Template.Child()
    _overview_text = Gtk.Template.Child()
    _seasons_group = Gtk.Template.Child()
    _status_entry = Gtk.Template.Child()
    _original_language_comborow = Gtk.Template.Child()
    _language_model = Gtk.Template.Child()
    _original_title_entry = Gtk.Template.Child()
    _budget_spinrow = Gtk.Template.Child()
    _revenue_spinrow = Gtk.Template.Child()
    _production_checkbtn = Gtk.Template.Child()

    __gsignals__ = {
        'edit-saved': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
    }

    seasons: list = []

    def __init__(self,
                 parent: Gtk.Window,
                 edit_mode: bool = False,
                 content: MovieModel | SeasonModel | None = None
                 ):
        super().__init__()
        self.set_transient_for(parent)

        self.edit_mode = edit_mode
        self._content = content

        if edit_mode and type(self._content) is MovieModel:
            self.set_title(_('Edit Movie'))
        elif edit_mode and type(self._content) is SeriesModel:
            self.set_title(_('Edit TV Series'))

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data: object | None) -> None:
        """
        Callback for the "map" signal.
        Setup the window by selecting the initial view (movies or tv series), the image for the poster and populates the language dropdown and the selected date for the release.

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        self._overview_text.remove_css_class('view')

        languages = local.get_all_languages()
        languages.insert(0, languages.pop(len(languages)-6))    # move 'no language' to 1st place
        for language in languages:
            self._language_model.append(language.name)

        self._poster.set_blank_image(f'resource://{shared.PREFIX}/blank_poster.jpg')

        if not self._content:
            if shared.schema.get_string('win-tab') == 'movies':
                self._movies_btn.set_active(True)
            else:
                self._series_btn.set_active(True)

            self._release_date_menu_btn.set_label(self._calendar.get_date().format('%x'))
            return

        # Both Movies and TV Series
        self._poster.set_image(self._content.poster_path)
        self._title_entry.set_text(self._content.title)
        self._title_entry.grab_focus()
        self._release_date_menu_btn.set_label(date.fromisoformat(self._content.release_date).strftime('%x'))
        self._calendar.select_day(GLib.DateTime.new_from_iso8601(
            datetime.fromisoformat(self._content.release_date).isoformat()+'Z'))
        self._genres_entry.set_text(', '.join(self._content.genres))
        self._tagline_entry.set_text(self._content.tagline)
        self._overview_text.get_buffer().set_text(self._content.overview, -1)
        self._status_entry.set_text(self._content.status)
        self._original_language_comborow.set_selected(
            self._get_selected_language_index(self._content.original_language))
        self._original_title_entry.set_text(self._content.original_title)

        # Movies specific
        if type(self._content) is MovieModel:
            self._movies_btn.set_active(True)
            self._runtime_spinrow.set_value(self._content.runtime)
            self._budget_spinrow.set_value(self._content.budget)
            self._revenue_spinrow.set_value(self._content.revenue)

        # TV Series specific
        if type(self._content) is SeriesModel:
            self._series_btn.set_active(True)
            self._creator_entry.set_text(','.join(self._content.created_by))
            self._production_checkbtn.set_active(self._content.in_production)
            self.seasons = self._parse_seasons(self._content.seasons)
            self.update_seasons_ui()

    def _parse_seasons(self, seasons_as_model: List[SeasonModel]) -> List[tuple]:
        """
        Parse seasons passed as a list of SeasonModels into a list of tuples.

        Args:
            seasons_as_model(List[SeasonModel]): a list of SeasonModels

        Returns:
            a list of tuples rappresenting the same data
        """

        seasons_as_tuple = []
        for season in seasons_as_model:

            episodes_as_tuple = []
            for episode in season.episodes:
                episodes_as_tuple.append((
                    episode.title, episode.number, episode.runtime, episode.overview, episode.still_path
                ))

            seasons_as_tuple.append((
                season.title,
                season.poster_path,
                episodes_as_tuple
            ))
        return seasons_as_tuple

    def _get_selected_language_index(self, language: LanguageModel) -> int:
        """
        Loops languages looking for the index of the provided language.

        Args:
            language (LanguageModel): language to look for

        Returns:
            index (int)
        """

        for idx in range(0, self._language_model.get_n_items()):
            if language.name == self._language_model.get_string(idx):
                return idx
        return -1

    @Gtk.Template.Callback('_on_title_changed')
    def _on_title_changed(self, user_data: object | None) -> None:
        """
        Callback for "changed" signal.
        Wrapper around self._enable_save_btn().

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        self._enable_save_btn()

    @Gtk.Template.Callback('_on_movies_btn_toggled')
    def _on_movies_btn_toggled(self, user_data: object | None) -> None:
        """
        Callback for "toggled" signal.
        Wrapper around self._enable_save_btn().

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        self._enable_save_btn()

    def _enable_save_btn(self) -> None:
        """
        Checks whether the "save" button should be active or not.

        Args:
            None

        Returns:
            None
        """

        # Movies: title required
        if self._movies_btn.get_active() and self._title_entry.get_text():
            self._save_btn.set_sensitive(True)
            return

        # TV Series: title and at least a season required
        if self._series_btn.get_active() and self._title_entry.get_text() and len(self.seasons) > 0:
            self._save_btn.set_sensitive(True)
            return

        self._save_btn.set_sensitive(False)

    @Gtk.Template.Callback('_on_calendar_day_selected')
    def _on_calendar_day_selected(self, user_data: object | None) -> None:
        """
        Callback for the "day-selected" signal.
        Sets the button's label as the selected date (user locale format)

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        self._release_date_menu_btn.set_label(self._calendar.get_date().format('%x'))

    @Gtk.Template.Callback('_on_season_add_btn_clicked')
    def _on_season_add_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for the "clicked" signal.
        Opens the "edit season" dialog.

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        # TRANSLATORS: {num} is the season number
        dialog = EditSeasonDialog(self, title=_('Season {num}').format(num=len(self.seasons)+1))
        dialog.connect('edit-saved', self._on_edit_saved)
        dialog.present()

    def _on_edit_saved(self, source: Gtk.Widget, title: str, poster_uri: str, episodes: List[tuple]) -> None:
        """
        Callback for the "edit-saved" signal.
        Appends the recieved data as a tuple in the seasons list and updates the ui.

        Args:
            source (Gtk.Widget): caller widget
            title (str): season title
            poster_uri (str): season poster uri
            episodes (List[tuple]): season episodes

        Returns:
            None
        """

        self.seasons.append((title, poster_uri, episodes))
        self.update_seasons_ui()

    @Gtk.Template.Callback('_on_done_btn_clicked')
    def _on_done_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for the "clicked" signal.
        Adds a background activity to add/update the content and closes the window.

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        if not self.edit_mode:
            BackgroundQueue.add(BackgroundActivity(  # TRANSLATORS: {title} is the content's title
                ActivityType.ADD, _('Add {title}').format(title=self._title_entry.get_text()), self._add_content_to_db))
        else:
            BackgroundQueue.add(BackgroundActivity(  # TRANSLATORS: {title} is the content's title
                ActivityType.UPDATE, _('Update {title}').format(title=self._title_entry.get_text()), self._add_content_to_db))

        self.close()

    def _add_content_to_db(self, activity: BackgroundActivity) -> None:
        """
        Copies the poster image to the data folder, saves the content, and refreshes the main window.

        Args:
            activity (BackgroundActivity): the calling activity

        Returns:
            None
        """

        poster_uri = self._copy_image_to_data(self._poster.get_uri(),
                                              shared.poster_dir,
                                              self._title_entry.get_text()
                                              ) if not self.edit_mode else self._content.poster_path  # type: ignore

        if self._movies_btn.get_active():
            self._save_movie(poster_uri)
        else:
            self._save_series(poster_uri)

        self.get_ancestor(Adw.Window).get_transient_for().activate_action('win.refresh', None)
        activity.end()

    def _save_movie(self, poster_uri: str) -> None:
        """
        Creates a MovieModel with the provided data and saves or updates the movie in the local db.

        Args:
            poster_uri (str): movie poster uri

        Returns:
            None
        """

        buffer = self._overview_text.get_buffer()
        start_iter = buffer.get_start_iter()
        end_iter = buffer.get_end_iter()
        overview = buffer.get_text(start_iter, end_iter, False)

        movie = MovieModel(t=(
            datetime.now(),                                                             # add date
            '',                                                                         # background
            int(self._budget_spinrow.get_value()),                                      # budget
            ''.join(self._genres_entry.get_text().split()),                             # genres
            local.get_next_manual_movie() if not self.edit_mode else self._content.id,  # id        # type: ignore
            True,                                                                       # manual
            local.get_language_by_name(self._original_language_comborow.get_selected_item(
            ).get_string()).iso_name,                                    # type: ignore # original language
            self._original_title_entry.get_text(),                                      # original title
            overview,                                                                   # overview
            poster_uri,                                                                 # poster
            self._calendar.get_date().format('%Y-%m-%d'),                               # release date
            int(self._revenue_spinrow.get_value()),                                     # revenue
            int(self._runtime_spinrow.get_value()),                                     # runtime
            self._status_entry.get_text(),                                              # status
            self._tagline_entry.get_text(),                                             # tagline
            self._title_entry.get_text(),                                               # title
            False if not self.edit_mode else self._content.watched       # type: ignore # watched
        ))

        if not self.edit_mode:
            local.add_movie(movie=movie)
        else:
            local.update_movie(old=self._content, new=movie)
            self.emit('edit-saved', movie)

    def _save_series(self, series_poster_uri: str) -> None:
        """
        Creates a SeriesModel with associated SeasonModels/EpisodeModels with the provided data and saves or updates the TV series in the local db.

        Args:
            poster_uri (str): tv series poster uri

        Returns:
            None
        """

        show_id = local.get_next_manual_series()
        base_season_id = local.get_next_manual_season()
        base_episode_id = local.get_next_manual_episode()

        seasons = []
        for idx, season in enumerate(self.seasons):

            # Create folder to store the images, if needed
            if not os.path.exists(f'{shared.series_dir}/{show_id}/{self._increment_manual_id(base_season_id, idx)}'):
                os.makedirs(f'{shared.series_dir}/{show_id}/{self._increment_manual_id(base_season_id, idx)}')

            # Copy the season poster
            poster_uri = self._copy_image_to_data(season[1],
                                                  f'{shared.series_dir}/{show_id}/{self._increment_manual_id(base_season_id, idx)}',
                                                  season[0])

            episodes = []
            for jdx, episode in enumerate(season[2]):

                # Copy the episode still
                still_uri = self._copy_image_to_data(episode[4],
                                                     f'{shared.series_dir}/{show_id}/{self._increment_manual_id(base_season_id, idx)}',
                                                     episode[0]
                                                     )
                episode_id = self._increment_manual_id(base_episode_id, jdx)
                season_number = idx+1
                watched = False

                episodes.append(EpisodeModel(t=(
                    episode_id,     # id
                    episode[1],     # episode number
                    episode[3],     # overview
                    episode[2],     # runtime
                    season_number,  # season number
                    show_id,        # show id
                    still_uri,      # still uri
                    episode[0],     # title
                    watched         # watched
                )))

            base_episode_id = self._increment_manual_id(base_episode_id, len(episodes)+1)
            season_id = self._increment_manual_id(base_season_id, idx)
            season_number = idx+1

            seasons.append(SeasonModel(t=(
                len(episodes),  # episodes number
                season_id,      # id
                season_number,  # season number
                '',             # overview
                poster_uri,     # season poster
                season[0],      # title
                show_id,        # show id
                episodes        # season episodes
            )))

        buffer = self._overview_text.get_buffer()
        start_iter = buffer.get_start_iter()
        end_iter = buffer.get_end_iter()
        overview = buffer.get_text(start_iter, end_iter, False)

        serie = SeriesModel(t=(
            datetime.now(),                                  # add date
            '',                                              # backgroud
            self._creator_entry.get_text(),                  # created by
            self._compute_episode_number(seasons),           # episode number
            ''.join(self._genres_entry.get_text().split()),  # genres
            show_id,                                         # id
            self._production_checkbtn.get_active(),          # in production
            True,                                            # manual
            local.get_language_by_name(self._original_language_comborow.get_selected_item(
            ).get_string()).iso_name,         # type: ignore # original language
            self._original_title_entry.get_text(),           # original title
            overview,                                        # overview
            series_poster_uri,                               # poster
            self._calendar.get_date().format('%Y-%m-%d'),    # release date
            len(seasons),                                    # seasons number
            self._status_entry.get_text(),                   # status
            self._tagline_entry.get_text(),                  # tagline
            self._title_entry.get_text(),                    # title
            False,                                           # watched
            seasons                                          # seasons
        ))

        if self.edit_mode:
            local.delete_series(self._content.id)   # type: ignore
            local.add_series(serie=serie)
            self.emit('edit-saved', serie)
        else:
            local.add_series(serie=serie)

    def _increment_manual_id(self, id: str, amount: int = 1) -> str:
        """
        Increments the integer part of a manual id by amount.

        Args:
            id (str): id to increment
            amount (int): how much to increment by

        Returns:
            the incremented id
        """

        tmp = id.split('-')
        return f'M-{int(tmp[1]) + amount}'

    def _compute_episode_number(self, seasons: List[SeasonModel]) -> int:
        """
        Counts the total number of episodes of a tv series.

        Args:
            seasons (List[SeasonModel]): seasons to loop on

        Returns:
            the total number of episodes
        """

        num = 0
        for season in seasons:
            for episode in season.episodes:
                num += 1
        return num

    def _copy_image_to_data(self, src_uri: str, dest_folder: str, filename: str) -> str:
        """
        Copies src_uri to dest_folder as filename. If src_uri is a resource (empty poster/still) the operation is not
        carried out.
        dest_folder must already exist on file system.

        Args:
            src_uri (str): source file uri
            dest_folder (str): path to the destination folder
            filename (str): new name for the copied file

        Returns:
            uri of the copied file or src_uri if is a resource.
        """

        if src_uri.startswith('file'):
            extension = src_uri[src_uri.rindex('.'):]
            shutil.copy2(src_uri[7:], f'{dest_folder}/{unquote(filename)}{extension}')
            return f'file://{dest_folder}/{unquote(filename)}{extension}'
        return src_uri

    def update_seasons_ui(self) -> None:
        """
        Rebuilds the ui to reflect changes to seasons.

        Args:
            None

        Returns:
            None
        """

        # Empty PreferencesGroup
        list_box = self._seasons_group.get_first_child().get_last_child().get_first_child()  # ugly workaround
        list_box.remove_all()

        # Fill PreferencesGroup
        for season in self.seasons:
            self._seasons_group.add(SeasonExpander(season_title=season[0], poster_uri=season[1], episodes=season[2]))

        self._enable_save_btn()

    def get_season(self,
                   title: str,
                   uri: str,
                   episodes: List[tuple]) -> tuple:
        """
        Compares and retrieves the tuple containing the passed data.

        Args:
            title (str): a title
            uri (str): an uri
            episodes (List[tuple]): a list of tuples rappresenting episodes

        Returns:
            tuple matching the passed data
        """

        for season in self.seasons:
            if (season[0] == title and
                season[1] == uri and
                    season[2] == episodes):
                return season
        return ()
