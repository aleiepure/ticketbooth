# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _
from typing import List

from gi.repository import Adw, GObject, Gtk

from .. import shared  # type: ignore
from ..dialogs.edit_episode_dialog import EditEpisodeNavigationPage
from ..widgets.episode_row import EpisodeRow


@Gtk.Template(resource_path=shared.PREFIX + '/ui/dialogs/edit_season.ui')
class EditSeasonDialog(Adw.Window):
    """
    This class rappresents the window to edit a season.

    Properties:
        None

    Methods:
        update_episodes_ui(): rebuilds the ui to reflect changes to episodes

    Signals:
        edit-saved (title: str, poster_uri: str, episodes: List[tuple]): emited when the user clicks the save button
    """

    __gtype_name__ = 'EditSeasonDialog'

    _navigation_view = Gtk.Template.Child()
    _save_btn = Gtk.Template.Child()
    _poster = Gtk.Template.Child()
    _title_entry = Gtk.Template.Child()
    _episodes_group = Gtk.Template.Child()

    __gsignals__ = {
        'edit-saved': (GObject.SIGNAL_RUN_FIRST, None, (str, str, object,)),
    }

    def __init__(self,
                 parent: Gtk.Window,
                 title: str = _('Season'),
                 poster_uri: str = f'resource://{shared.PREFIX}/blank_poster.jpg',
                 episodes: List[tuple] | None = None):

        super().__init__()
        self.set_transient_for(parent)

        self._title = title
        self._poster_uri = poster_uri
        self._episodes = episodes if episodes else []

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data: object | None) -> None:
        """
        Callback for "map" signal.
        Sets the title text and poster image, populates the episode data.

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        self._title_entry.set_text(self._title)
        self._poster.set_blank_image(self._poster_uri)

        for episode in self._episodes:
            self._episodes_group.add(EpisodeRow(title=episode[0],
                                                episode_number=episode[1],
                                                runtime=episode[2],
                                                overview=episode[3],
                                                still_uri=episode[4],
                                                editable=True)
                                     )

    @Gtk.Template.Callback('_on_title_entry_changed')
    def _on_title_entry_changed(self, user_data: object | None) -> None:
        """
        Callback for "changed" signal.
        Wrap around to call self._enable_save_btn().

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        self._enable_save_btn()

    def _enable_save_btn(self) -> None:
        """
        Checks whether the "save" button should be made active or not.

        Args:
            None

        Returns:
            None
        """

        if self._title_entry.get_text() and len(self._episodes) > 0:
            self._save_btn.set_sensitive(True)
            return

        self._save_btn.set_sensitive(False)

    @Gtk.Template.Callback('_on_save_btn_clicked')
    def _on_save_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for "clicked" signal.
        Emits the "edit-saved" signal and closes the window.

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        self.emit('edit-saved', self._title_entry.get_text(), self._poster.get_uri(), self._episodes)
        self.close()

    @Gtk.Template.Callback('_on_add_btn_clicked')
    def _on_add_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for "clicked" signal.
        Shows the "edit episode" page.

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        edit_episode_page = EditEpisodeNavigationPage(episode_number=len(self._episodes)+1)
        edit_episode_page.connect('edit-saved', self._on_episode_saved)
        self._navigation_view.push(edit_episode_page)

    def _on_episode_saved(self,
                          source: Gtk.Widget,
                          title: str,
                          episode_number: int,
                          runtime: int,
                          overview: str,
                          still_uri: str) -> None:
        """
        Callback for "edit-saved" signal.
        Appends the recieved data as a tuple in the episodes list and updates the ui.

        Args:
            source (Gtk.Widget): caller widget
            title (str): epiosode title
            episode_number (int): episode number
            runtime (int): episode runtime in minutes
            overview (str): episode overview
            still_uri (str): episode still uri

        Returns:
            None
        """

        self._episodes.append((title, episode_number, runtime, overview, still_uri))
        self.update_episodes_ui()

    def update_episodes_ui(self) -> None:
        """
        Rebuilds the ui to reflect changes to episodes.

        Args:
            None

        Returns:
            None
        """

        # Empty PreferencesGroup
        list_box = self._episodes_group.get_first_child().get_last_child().get_first_child()  # ugly workaround
        for child in list_box:
            self._episodes_group.remove(child)

        # Fill PreferencesGroup
        for episode in self._episodes:
            self._episodes_group.add(EpisodeRow(title=episode[0],
                                                episode_number=episode[1],
                                                runtime=episode[2],
                                                overview=episode[3],
                                                still_uri=episode[4],
                                                editable=True))
        self._enable_save_btn()

    def get_episode(self, title, episode_number, runtime, overview, still_uri):
        for episode in self.episodes:
            if (episode[0] == title and
                episode[1] == episode_number and
                episode[2] == runtime and
                episode[3] == overview and
                    episode[4] == still_uri):
                return episode
        return ()
