# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _
from gettext import pgettext as C_
from typing import List

from gi.repository import Adw, Gio, GObject, Gtk

import src.dialogs.add_manual_dialog as dialog

from .. import shared  # type: ignore
from ..dialogs.edit_season_dialog import EditSeasonDialog
from ..widgets.episode_row import EpisodeRow


@Gtk.Template(resource_path=shared.PREFIX + '/ui/widgets/season_expander.ui')
class SeasonExpander(Adw.ExpanderRow):
    """
    This class rappresents a season in the manual add window.

    Properties:
        season_title (str): season title
        poster_uri (str): season poster uri

    Methods:
        None

    Signals:
        None
    """

    __gtype_name__ = 'SeasonExpander'

    season_title = GObject.Property(type=str)
    poster_uri = GObject.Property(type=str)
    episodes = GObject.Property(type=object)

    _poster = Gtk.Template.Child()

    def __init__(self,
                 season_title: str = _('Season'),
                 poster_uri: str = f'resource://{shared.PREFIX}/blank_poster.jpg',
                 episodes: List | None = None):

        super().__init__()

        self.season_title = season_title
        self.poster_uri = poster_uri
        self.episodes = episodes if episodes else []

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data: object | None) -> None:
        """
        Callback for "map" signal.
        Sets the poster image and populates the episode data.

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        self._poster.set_file(Gio.File.new_for_uri(self.poster_uri))

        for episode in self.episodes:
            self.add_row(EpisodeRow(title=episode[0],
                                    episode_number=episode[1],
                                    runtime=episode[2],
                                    overview=episode[3],
                                    still_uri=episode[4],
                                    show_controls=False)
                         )

    @Gtk.Template.Callback('_on_edit_btn_clicked')
    def _on_edit_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for "clicked" signal.
        Shows the "edit season" window.

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        dialog = EditSeasonDialog(self.get_ancestor(Gtk.Window), title=self.season_title,
                                  poster_uri=self.poster_uri, episodes=self.episodes)
        dialog.connect('edit-saved', self._on_edit_saved)
        dialog.present()

    def _on_edit_saved(self,
                       source: Gtk.Widget,
                       title: str,
                       poster_uri: str,
                       episodes: List[tuple]) -> None:
        """
        Callback for "edit-saved" signal.
        Appends the recieved data as a tuple in the seasons list after removing the changed one and updates the ui.

        Args:
            source (Gtk.Widget): caller widget
            title (str): season title
            poster_uri (str): season poster uri
            episodes (List[tuple]): episodes in season

        Returns:
            None
        """

        parent_dialog = self.get_ancestor(dialog.AddManualDialog)

        old_season = parent_dialog.get_season(self.season_title,
                                              self.poster_uri,
                                              self.episodes)
        parent_dialog.seasons.remove(old_season)

        parent_dialog.seasons.append((title, poster_uri, episodes))

        parent_dialog.update_seasons_ui()

    @Gtk.Template.Callback('_on_delete_btn_clicked')
    def _on_delete_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for the "clicked" signal.
        Asks the user for a confirmation after a delete request.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        # TRANSLATORS: {title} is the showed content's title
        dialog = Adw.MessageDialog.new(self.get_ancestor(Adw.Window),
                                       C_('message dialog heading', 'Delete {title}?').format(title=self.season_title),
                                       C_('message dialog body', 'This season contains unsaved metadata.')
                                       )
        dialog.add_response('cancel', C_('message dialog action', '_Cancel'))
        dialog.add_response('delete', C_('message dialog action', '_Delete'))
        dialog.set_response_appearance('delete', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.choose(None, self._on_message_dialog_choose, None)

    def _on_message_dialog_choose(self, source: GObject.Object | None, result: Gio.AsyncResult, user_data: object | None) -> None:
        """
        Callback for the message dialog.
        Finishes the async operation and retrieves the user response. If the later is positive, delete the content from the db.

        Args:
            source (Gtk.Widget): object that started the async operation
            result (Gio.AsyncResult): a Gio.AsyncResult
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        result = Adw.MessageDialog.choose_finish(source, result)
        if result == 'cancel':
            return

        parent_dialog = self.get_ancestor(dialog.AddManualDialog)
        old_season = parent_dialog.get_season(self.season_title, self.poster_uri, self.episodes)
        parent_dialog.seasons.remove(old_season)
        parent_dialog.update_seasons_ui()
