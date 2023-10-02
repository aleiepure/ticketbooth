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
    task_function = GObject.Property(type=object, default=None)
    completed = GObject.Property(type=bool, default=False)
    has_error = GObject.Property(type=bool, default=False)

    def __init__(self, activity_type: ActivityType, title: str = '', task_function: Callable | None = None):
        super().__init__()
        self.activity_type = activity_type.name
        self.title = title
        self.task_function = task_function
        self._cancellable = Gio.Cancellable()

    def start(self, on_done: Callable) -> None:
        """
        Runs self.callback in a separate thread. The callback must call end() to mark the activity as completed.

        Args:
            None

        Returns:
            None
        """

        task = Gio.Task.new(self, None, on_done, self._cancellable, self)
        task.set_return_on_cancel(True)
        task.run_in_thread(self._run_in_thread)

    def _run_in_thread(self,
                       task: Gio.Task,
                       source_object: GObject.Object,
                       task_data: object | None,
                       cancelable: Gio.Cancellable):
        """Callback to run self.task_function in a thread"""

        if task.return_error_if_cancelled():
            return
        outcome = self.task_function(self)  # type: ignore
        task.return_value(outcome)

    def activity_finish(self, result: Gio.AsyncResult, caller: GObject.Object):
        """
        Completes the async operation and marks the activity as completed.

        Args:
            None

        Returns:
            None
        """

        if not Gio.Task.is_valid(result, caller):
            return -1

        # self.completed = True
        return result.propagate_value().value

    def end(self) -> None:
        """
        Marks the activity as completed.

        Args:
            None

        Returns:
            None
        """

        self.completed = True

    def error(self) -> None:
        """
        Marks the activity with an error.

        Args:
            None

        Returns:
            None
        """

        self.has_error = True


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
    def add(activity: BackgroundActivity, on_done: Callable) -> None:
        """
        Adds an activity to the queue and starts its execution.

        Args:
            activity (BackgroundActivity): the activity to add

        Returns:
            None
        """

        BackgroundQueue._queue.append(activity)
        activity.start(on_done)

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
