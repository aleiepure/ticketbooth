# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from enum import Enum
from typing import Callable

from gi.repository import Gio, GLib, GObject

from . import shared  # type: ignore


class ActivityType(Enum):
    """
    Enum for the types of background activities
    """

    ADD = 0
    REMOVE = 1
    UPDATE = 2


class BackgroundActivity(GObject.GObject):
    """
    An activity that is run in the background.

    Properties:
        title (str): a title
        activity_type (str): an activity type, name as in ActivityType
        callback (callable): a function to run in the background
        completed (bool): indicates if the activity is completed

    Methods:
        start(): runs self.callback in a separate thread
        end(): marks the activity as completed

    Signals:
        None
    """

    __gtype_name__ = 'BackgroundActivity'

    title = GObject.Property(type=str, default='')
    activity_type = GObject.Property(type=str, default='')
    callback = GObject.Property(type=object, default=None)
    completed = GObject.Property(type=bool, default=False)

    def __init__(self, activity_type: ActivityType, title: str = '', callback: Callable | None = None):
        super().__init__()
        self.activity_type = activity_type.name
        self.title = title
        self.callback = callback

    def start(self) -> None:
        """
        Runs self.callback in a separate thread. The callback must call end() to mark the activity as completed.

        Args:
            None

        Returns:
            None
        """

        try:
            GLib.Thread.try_new(self.title, self.callback, self)
        except GLib.Error as err:
            shared.logging.error(err)
            raise err

    def end(self) -> None:
        """
        Marks the activity as completed.

        Args:
            None

        Returns:
            None
        """

        self.completed = True


class BackgroundQueue:
    """
    A queue of background activities.

    Properties:
        None

    Methods:
        add(activity: BackgroundActivity): adds an activity to the queue
        get_queue(): returns the queue

    Signals:
        None
    """

    _queue = Gio.ListStore.new(item_type=BackgroundActivity)

    @staticmethod
    def add(activity: BackgroundActivity) -> None:
        """
        Adds an activity to the queue and starts its execution.

        Args:
            activity (BackgroundActivity): the activity to add

        Returns:
            None
        """

        BackgroundQueue._queue.append(activity)
        activity.start()

    @staticmethod
    def get_queue() -> Gio.ListStore:
        """
        Returns the queue

        Args:
            None

        Returns:
            the queue (a Gio.ListStore)
        """

        return BackgroundQueue._queue
