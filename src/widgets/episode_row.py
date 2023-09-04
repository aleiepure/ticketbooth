# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _
from gettext import pgettext as C_

from gi.repository import Adw, Gio, GObject, Gtk

import src.dialogs.edit_season_dialog as dialog

from .. import shared  # type: ignore
from ..models.episode_model import EpisodeModel
from ..pages.edit_episode_page import EditEpisodeNavigationPage


@Gtk.Template(resource_path=shared.PREFIX + '/ui/widgets/episode_row.ui')
class EpisodeRow(Adw.PreferencesRow):
    """
    Widget that represents an episode inside the season expander row.

    Properties:
        title (str): episode title
        episode_number (int): episode number in a season
        runtime (int): episode runtime in minutes
        overview (str): episode overview
        still_uri (str): episode still image uri
        editable (bool): whether or not to show delete and edit buttons instead of the "watched" checkbutton
        show_controls (bool): whether or not to show the suffix widgets

    Methods:
        None

    Signals:
        toggled(active: bool): emited when the user toggles the checkbox
    """

    __gtype_name__ = 'EpisodeRow'

    title = GObject.Property(type=str, default='')
    episode_number = GObject.Property(type=int, default=0)
    runtime = GObject.Property(type=int, default=0)
    overview = GObject.Property(type=str, default='')
    still_uri = GObject.Property(type=str, default='')
    editable = GObject.Property(type=bool, default=False)
    show_controls = GObject.Property(type=bool, default=True)

    __gsignals__ = {
        'toggled': (GObject.SIGNAL_RUN_FIRST, None, (bool,)),
    }

    _still_picture = Gtk.Template.Child()
    _runtime_lbl = Gtk.Template.Child()
    _title_lbl = Gtk.Template.Child()
    _check_btn = Gtk.Template.Child()

    def __init__(self,
                 episode: EpisodeModel | None = None,
                 title: str = '',
                 episode_number: int = 0,
                 runtime: int = 0,
                 overview: str = '',
                 still_uri: str = '',
                 editable: bool = False,
                 show_controls: bool = True):
        super().__init__()

        if episode:
            self.title = episode.title
            self.episode_number = episode.number
            self.runtime = episode.runtime
            self.overview = episode.overview
            self.still_uri = episode.still_path
        else:
            self.title = title
            self.episode_number = episode_number
            self.runtime = runtime
            self.overview = overview
            self.still_uri = still_uri

        self.editable = editable
        self.show_controls = show_controls

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data: object | None) -> None:
        """
        Callback for "map" signal.
        Sets the still image and title/runtime entries.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        self._still_picture.set_file(Gio.File.new_for_uri(self.still_uri))
        self._title_lbl.set_text(f'{self.episode_number}. {self.title}')
        self._runtime_lbl.set_text(self._format_runtime(self.runtime))

    @Gtk.Template.Callback('_on_check_btn_toggled')
    def _on_check_btn_toggled(self, user_data:  object | None) -> None:
        """
        Callback for "toggle" signal.
        Emits the "toggled" signal with the new state.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        self.emit('toggled', self._check_btn.get_active())

    def _format_runtime(self, runtime: int) -> str:
        """
        Formats the runtime in hours and minutes.

        Args:
            runtime (str): runtime in minutes

        Returns:
            formatted duration string in hours and minutes
        """

        h, m = divmod(runtime, 60)

        if h > 0:

            # TRANSLATORS: {h} and {m} are the runtime hours and minutes respectively
            return _('{h}h {m}min').format(h=h, m=m)
        else:

            # TRANSLATORS: {m} is the runtime minutes
            return _('{m}min').format(m=m)

    @Gtk.Template.Callback('_on_edit_btn_clicked')
    def _on_edit_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for "clicked" signal.
        Shows the "edit episode" page.

        Args:
            user_data (object or None): user data passed to the callback.

        Returns:
            None
        """

        edit_episode_page = EditEpisodeNavigationPage(title=self.title,
                                                      episode_number=self.episode_number,
                                                      runtime=self.runtime,
                                                      overview=self.overview,
                                                      still_uri=self.still_uri)
        edit_episode_page.connect('edit-saved', self._on_episode_saved)
        self.get_ancestor(Adw.NavigationView).push(edit_episode_page)

    def _on_episode_saved(self,
                          source: Gtk.Widget,
                          title: str,
                          episode_number: int,
                          runtime: int,
                          overview: str,
                          still_uri: str) -> None:
        """
        Callback for "edit-saved" signal.
        Appends the recieved data as a tuple in the episodes list after removing the changed one and updates the ui.

        Args:
            source (Gtk.Widget): caller widget
            title (str): episode title
            episode_number (int): episode number
            runtime (int): episode runtime in minutes
            overview (str): episode overview
            still_uri (str): episode still uri

        Returns:
            None
        """

        parent = self.get_ancestor(dialog.EditSeasonDialog)

        old_episode = parent.get_episode(self.title,
                                         self.episode_number,
                                         self.runtime,
                                         self.overview,
                                         self.still_uri)
        parent._episodes.remove(old_episode)
        parent.update_episodes_ui()

        parent._episodes.append((title, episode_number, runtime, overview, still_uri))

        parent.update_episodes_ui()

    @Gtk.Template.Callback('_on_delete_btn_clicked')
    def _on_delete_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for "clicked" signal.
        Asks the user for a confirmation after a delete request.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        # TRANSLATORS: {title} is the showed content's title
        dialog = Adw.MessageDialog.new(self.get_ancestor(Adw.Window),
                                       C_('message dialog heading', 'Delete {title}?').format(
                                           title=f'{self.episode_number}.{self.title}'),
                                       C_('message dialog body', 'All cheanges to this episode will be lost.')
                                       )
        dialog.add_response('cancel', C_('message dialog action', '_Cancel'))
        dialog.add_response('delete', C_('message dialog action', '_Delete'))
        dialog.set_response_appearance('delete', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.choose(None, self._on_message_dialog_choose, None)

    def _on_message_dialog_choose(self,
                                  source: GObject.Object | None,
                                  result: Gio.AsyncResult,
                                  user_data: object | None) -> None:
        """
        Callback for the message dialog.
        Finishes the async operation and retrieves the user response. If the later is positive, deletes the episode from the list and updates the ui.

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

        parent = self.get_ancestor(dialog.EditSeasonDialog)
        old_episode = parent.get_episode(self.title,
                                         self.episode_number,
                                         self.runtime,
                                         self.overview,
                                         self.still_uri)
        parent._episodes.remove(old_episode)
        parent.update_episodes_ui()
