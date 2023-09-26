# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gio, GObject, Gtk

from .. import shared  # type: ignore
from ..background_queue import BackgroundQueue


@Gtk.Template(resource_path=shared.PREFIX + '/ui/widgets/background_indicator.ui')
class BackgroundIndicator(Adw.Bin):
    """
    This class represents the indicator for background activities.

    Properties:
        queue (Gio.ListStore): the queue

    Methods:
        refresh(): updates the icon button

    Signals:
        None
    """

    __gtype_name__ = 'BackgroundIndicator'

    queue = GObject.Property(type=Gio.ListStore)

    _stack = Gtk.Template.Child()
    _model = Gtk.Template.Child()
    _image = Gtk.Template.Child()
    _spinner = Gtk.Template.Child()
    _list_view = Gtk.Template.Child()

    def __init__(self):
        super().__init__()
        self.queue = BackgroundQueue.get_queue()

        self._spinner.bind_property('visible', self._image, 'visible', GObject.BindingFlags.INVERT_BOOLEAN)
        self.queue.connect('notify::n-items', self._on_queue_change)

    def _on_queue_change(self, pspec: GObject.ParamSpec, user_data: object | None) -> None:
        """
        Callback for "notify::n-items" signal.
        Updates the model and refreshes the indicator.

        Args:
            pspec (GObject.ParamSpec): The GParamSpec of the property which changed
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        if self.queue.get_property('n-items') > 0:

            self._model.remove_all()
            for activity in self.queue:
                self._model.append(activity)

            self._stack.set_visible_child_name('filled')
            self.refresh()

    def refresh(self) -> None:
        """
        Checks the activities and shows a spinner as the button icon if at least one activity is running. If all activities are completed, the icon is set to a check mark.

        Args:
            None

        Returns:
            None
        """

        self._spinner.set_visible(not all(activity.completed for activity in self.queue))
