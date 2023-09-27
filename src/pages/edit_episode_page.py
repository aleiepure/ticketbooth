# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, GObject, Gtk

from .. import shared  # type: ignore
from ..models.episode_model import EpisodeModel


@Gtk.Template(resource_path=shared.PREFIX + '/ui/pages/edit_episode_page.ui')
class EditEpisodeNavigationPage(Adw.NavigationPage):
    """
    This class represents the 'edit episode' NavigationPane.

    Properties:
        None

    Methods:
        None

    Signals:
        edit-saved (title: str, episode_number: int, runtime: int, overview: str, still_uri: str): emited when the user clicks the save button
    """

    __gtype_name__ = 'EditEpisodeNavigationPage'

    _still = Gtk.Template.Child()
    _episode_spin_row = Gtk.Template.Child()
    _title_entry = Gtk.Template.Child()
    _runtime_spin_row = Gtk.Template.Child()
    _overview_text = Gtk.Template.Child()

    __gsignals__ = {
        'edit-saved': (GObject.SIGNAL_RUN_LAST, None, (str, int, int, str, str,)),
    }

    def __init__(self,
                 title: str = '',
                 episode_number: int = 0,
                 runtime: int = 0,
                 overview: str = '',
                 still_uri: str = f'resource://{shared.PREFIX}/blank_still.jpg'):

        super().__init__()

        self._title = title
        self._episode_number = episode_number
        self._runtime = runtime
        self._overview = overview
        self._still_uri = still_uri

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data: object | None) -> None:
        """
        Callback for "map" signal.
        Sets the fields/still image to the provided values

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        self._overview_text.remove_css_class('view')

        self._title_entry.set_text(self._title)
        self._runtime_spin_row.set_value(self._runtime)
        self._still.set_blank_image(f'resource://{shared.PREFIX}/blank_still.jpg')
        if self._still_uri.startswith('file'):
            self._still.set_image(self._still_uri)
        self._overview_text.get_buffer().set_text(self._overview, -1)
        self._episode_spin_row.set_value(self._episode_number)

        self._title_entry.grab_focus()

    @Gtk.Template.Callback('_enable_save')
    def _enable_save(self, source: Gtk.Widget, title: str, episode_number: int) -> bool:
        """
        Closure to determine if the 'save' button should be enabled or not.

        Args:
            source (Gtk.Widget): caller widget
            title (str): title text
            episode_number (int): episode number

        Returns:
            bool
        """

        return True if title and episode_number > 0 else False

    @Gtk.Template.Callback('_on_save_btn_clicked')
    def _on_save_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for the "clicked" signal.
        Emits the "edit-saved" signal and pops the NavigationPage.

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        buffer = self._overview_text.get_buffer()
        start_iter = buffer.get_start_iter()
        end_iter = buffer.get_end_iter()

        overview = buffer.get_text(start_iter, end_iter, False)
        title = self._title_entry.get_text()
        episode_number = int(self._episode_spin_row.get_value())
        runtime = int(self._runtime_spin_row.get_value())
        still_uri = self._still.get_uri()

        self.emit('edit-saved', title, episode_number, runtime, overview, still_uri)
        self.get_ancestor(Adw.NavigationView).pop()
