# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, GObject, Gtk

from .. import shared  # type: ignore


@Gtk.Template(resource_path=shared.PREFIX + '/ui/widgets/background_activity_row.ui')
class BackgroundActivityRow(Adw.Bin):
    """
    This class represents a row in the BackgroundIndicator popover.

    Properties:
        title (str): a title
        activity_type (str): an activity type, name as in ActivityType
        completed (bool): indicates if the activity is completed

    Methods:
        None

    Signals:
        None
    """

    __gtype_name__ = 'BackgroundActivityRow'

    title = GObject.Property(type=str, default='')
    activity_type = GObject.Property(type=str, default='')
    completed = GObject.Property(type=bool, default=False)
    has_error = GObject.Property(type=bool, default=False)

    _icon = Gtk.Template.Child()
    _progress_bar = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

        self.connect('notify::completed', self._on_complete)

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data: object | None) -> None:
        """
        Callback for "map" signal.
        Sets the icon based on the completion status and activity type, and starts the progress bar.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        if not self.completed:
            match self.activity_type:
                case 'ADD':
                    self._icon.set_from_icon_name('plus')
                case 'REMOVE':
                    self._icon.set_from_icon_name('user-trash-symbolic')
                case 'UPDATE':
                    self._icon.set_from_icon_name('update')
            GObject.timeout_add(500, self._on_timeout, None)
        else:
            if self.has_error:
                self._progress_bar.add_css_class('progress_error')
                self._icon.set_from_icon_name('warning')
            else:
                self._progress_bar.add_css_class('progress_complete')
                self._icon.set_from_icon_name('check-plain')
            self._progress_bar.set_fraction(1)

    def _on_timeout(self, user_data: object | None) -> bool:
        """
        Callback for GObject.timeout_add.
        Pulses the progress bar.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            True if the timeout should be called again, False otherwise
        """

        if not self.completed:
            self._progress_bar.pulse()
            return True
        else:
            return False

    def _on_complete(self, pspec: GObject.ParamSpec, user_data: object | None) -> None:
        """
        Callback for "notify::completed" signal.
        Sets the icon and progres bar to show a completed status, updates the background indicator.

        Args:
            pspec (GObject.ParamSpec): The GParamSpec of the property which changed
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        self._icon.set_from_icon_name('check-plain')
        self._progress_bar.set_fraction(1)

        if self.get_ancestor(Adw.ApplicationWindow):
            self.get_ancestor(Adw.ApplicationWindow).activate_action(
                'win.update-backgroud-indicator')
