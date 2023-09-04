# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

# isort: off
# autopep8: off
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
# isort: on
# autopep: on

import sys
from gettext import gettext as _
from typing import Callable

from gi.repository import Adw, Gio, GObject, Gtk

from . import shared  # type: ignore
from .models.search_result_model import SearchResultModel
from .preferences import PreferencesWindow
from .views.content_view import ContentView
from .views.first_run_view import FirstRunView
from .views.main_view import MainView
from .widgets.episode_row import EpisodeRow
from .widgets.image_selector import ImageSelector
from .widgets.poster_button import PosterButton
from .widgets.search_result_row import SearchResultRow
from .window import TicketboothWindow


class TicketboothApplication(Adw.Application):
    """The main application singleton class."""

    # Types used in blueprint files
    _custom_widgets = [
        SearchResultModel,
        PosterButton,
        SearchResultRow,
        FirstRunView,
        MainView,
        ContentView,
        EpisodeRow,
        ImageSelector,
    ]

    def __init__(self):
        super().__init__(application_id=shared.APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)

        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action)

        for i in self._custom_widgets:
            GObject.type_ensure(i)

    def do_activate(self):
        """
        Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = TicketboothWindow(application=self)
        win.present()
    def on_about_action(self, widget: Gtk.Widget, user_data: object | None):
        """Callback for the app.about action."""

        builder = Gtk.Builder.new_from_resource(shared.PREFIX + '/ui/about_window.ui')
        about_window = builder.get_object('about_window')
        about_window.set_application_name(shared.APP_NAME)
        about_window.set_application_icon(shared.APP_ID)
        about_window.set_version(shared.VERSION)
        about_window.set_transient_for(self.props.active_window)
        about_window.add_credit_section('Contributors', [])
        about_window.add_legal_section('Movie and TV Series Metadata', 'This product uses the TMDB API but is not endorsed or certified by TMDB.', Gtk.License.CUSTOM, 'All rights belong to their respective owners.')
        about_window.present()

    def on_preferences_action(self, widget: Gtk.Widget, user_data: object | None):
        """Callback for the app.preferences action."""

        pref_window = PreferencesWindow()
        pref_window.set_transient_for(self.props.active_window)
        pref_window.present()

    def create_action(self, name: Gtk.Widget, callback: Callable, shortcuts=None):
        """
        Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f'app.{name}', shortcuts)


def main():
    """The application's entry point."""
    app = TicketboothApplication()
    return app.run(sys.argv)
