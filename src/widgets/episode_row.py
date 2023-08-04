# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _

from gi.repository import Adw, Gio, GObject, Gtk

from .. import shared  # type: ignore
from ..models.episode_model import EpisodeModel


@Gtk.Template(resource_path=shared.PREFIX + '/ui/widgets/episode_row.ui')
class EpisodeRow(Adw.Bin):
    """
    Widget that represents an episode inside the season expander row.

    Properties:
        episode (EpisodeModel): episode associated to the information shown

    Methods:
        None

    Signals:
        None
    """

    __gtype_name__ = 'EpisodeRow'

    episode = GObject.Property(type=EpisodeModel)

    __gsignals__ = {
        'toggled': (GObject.SIGNAL_RUN_FIRST, None, (bool,)),
    }

    _still_picture = Gtk.Template.Child()
    _runtime_lbl = Gtk.Template.Child()
    _title_lbl = Gtk.Template.Child()
    _check_btn = Gtk.Template.Child()

    def __init__(self, episode: EpisodeModel):
        super().__init__()
        self.episode = episode

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data: object | None) -> None:
        """
        Callback for "map" signal.
        Sets the still image and title/runtime labels.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        self._still_picture.set_file(Gio.File.new_for_uri(self.episode.still_path))
        self._title_lbl.set_text(f'{self.episode.number}. {self.episode.title}')
        self._runtime_lbl.set_text(self._format_runtime(self.episode.runtime))

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

            # TRANSLATORS: content runtime
            return _('{h}h {m}min').format(h=h, m=m)
        else:

            # TRANSLATORS: content runtime
            return _('{m}min').format(m=m)
