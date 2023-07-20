# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import sys

# isort: off
# autopep8: off
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw, Gio, Gtk
# isort: on
# autopep: on

from .window import TicketboothWindow


class TicketboothApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self, version, debug):
        super().__init__(application_id='me.iepure.ticketbooth',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)

        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action)

        self.version = version
        self.debug = debug

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = TicketboothWindow(self.debug, application=self)
        win.present()

    def on_about_action(self, widget, _):
        """Callback for the app.about action."""
        builder = Gtk.Builder.new_from_resource('/me/iepure/ticketbooth/ui/about_window.ui')
        about_window = builder.get_object('about_window')
        if self.debug == 'True':
            about_window.set_application_name(f'{about_window.get_application_name()}\n(Development snapshot)')
            about_window.set_icon_name('me.iepure.ticketbooth')
        about_window.set_version(self.version)
        about_window.set_transient_for(self.props.active_window)
        about_window.add_credit_section('Contributors', [])
        about_window.present()

    def on_preferences_action(self, widget, _):
        """Callback for the app.preferences action."""
        print('app.preferences action activated')

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect('activate', callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f'app.{name}', shortcuts)


def main(version, debug):
    """The application's entry point."""
    app = TicketboothApplication(version, debug)
    return app.run(sys.argv)
