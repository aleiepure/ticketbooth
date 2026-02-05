# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

# isort: off
# autopep8: off
import gi

from src.background_queue import ActivityType, BackgroundActivity, BackgroundQueue

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
# isort: on
# autopep: on

import logging
import os
import platform
import subprocess
import sys
from gettext import gettext as _
from gettext import pgettext as C_
from typing import Callable
from datetime import datetime 
import threading

from gi.repository import Adw, Gio, GObject, Gtk, GLib

from . import shared  # type: ignore
from .models.search_result_model import SearchResultModel
from .preferences import PreferencesDialog
from .views.content_view import ContentView
from .pages.details_page import DetailsView
from .views.first_run_view import FirstRunView
from .views.db_update_view import DbUpdateView
from .views.main_view import MainView
from .widgets.background_activity_row import BackgroundActivityRow
from .widgets.background_indicator import BackgroundIndicator
from .widgets.episode_row import EpisodeRow
from .widgets.image_selector import ImageSelector
from .widgets.poster_button import PosterButton
from .widgets.search_result_row import SearchResultRow
from .window import TicketboothWindow
from .providers.local_provider import LocalProvider as local

class TicketboothApplication(Adw.Application):
    """The main application singleton class."""

    # Types used in blueprint files
    _custom_widgets = [
        SearchResultModel,
        PosterButton,
        SearchResultRow,
        DetailsView,
        DbUpdateView,
        FirstRunView,
        MainView,
        ContentView,
        EpisodeRow,
        ImageSelector,
        BackgroundIndicator,
        BackgroundActivityRow,
    ]

    def __init__(self):
        super().__init__(application_id=shared.APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)

        logging.info('Ticket Booth started')
        logging.info(f'Debug: {shared.DEBUG}')
        logging.debug('Python version: %s', sys.version)
        if os.getenv('FLATPAK_ID') == shared.APP_ID:
            process = subprocess.run(
                ('flatpak-spawn', '--host', 'flatpak', '--version'),
                capture_output=True,
                encoding='utf-8',
                check=False,
            )
            logging.debug('Flatpak version: %s', process.stdout.rstrip())
        logging.debug('Platform: %s', platform.platform())
        if os.name == 'posix':
            for key, value in platform.uname()._asdict().items():
                logging.debug('\t%s: %s', key.title(), value)
        logging.debug('─' * 37)

        self.create_action('quit', lambda *_: self.quit(), ['<primary>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action, ['<primary>comma'])
        self.create_action('export', self.do_export)
        self.create_action('import', self.do_import)

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

        logging.debug('Window open')

        win.present()

    def on_about_action(self, widget: Gtk.Widget, user_data: object | None):
        """Callback for the app.about action."""

        builder = Gtk.Builder.new_from_resource(shared.PREFIX + '/ui/about_dialog.ui')
        about_dialog = builder.get_object('about_dialog')
        about_dialog.set_application_name(shared.APP_NAME)
        about_dialog.set_application_icon(shared.APP_ID)
        about_dialog.set_version(shared.VERSION)
        about_dialog.add_credit_section('Contributors', [
            # your name <your email>
            # your name website
        ])
        about_dialog.add_legal_section('Movie and TV Series Metadata', 'This product uses the TMDB API but is not endorsed or certified by TMDB.', Gtk.License.CUSTOM, 'All rights belong to their respective owners.')
        logging.debug('About window open')
        about_dialog.present(self.props.active_window)

    def on_preferences_action(self, widget: Gtk.Widget, user_data: object | None):
        """Callback for the app.preferences action."""

        pref_dialog = PreferencesDialog()
        logging.debug('Preferences dialog open')
        pref_dialog.present(self.props.active_window)

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
        logging.debug(f'Created action app.{name} ({shortcuts})')

    def do_export(self, widget: Gtk.Widget, user_data: object | None):
        """
        Callback for the app.export action

        Args:
            widget (Gtk.Widget): the widget that triggered the action
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        logging.info('Export requested')
        logging.info('Opening file dialog to select export location')
        self.dialog = Gtk.FileDialog.new()
        self.dialog.set_modal(True)
        self.dialog.set_initial_name(f"ticketbooth-export-{datetime.now().strftime('%Y-%m-%d-%H:%M:%S')}.zip")
        
        file_filter_store = Gio.ListStore.new(Gtk.FileFilter)
        file_filter = Gtk.FileFilter()
        file_filter.add_suffix("zip")
        file_filter_store.append(file_filter)

        self.dialog.set_filters(file_filter_store)
        self.dialog.save(self.props.active_window, None, self._on_file_save_complete, None)

    def _on_file_save_complete(self,
                               source: Gtk.Widget,
                               result: Gio.AsyncResult,
                               user_data: object | None) -> None:
        """
        Callback for the file dialog.
        Finishes the file selection and, if successfull, asks for confirmation

        Args:
            source (Gtk.Widget): caller widget
            result (Gio.AsyncResult): a Gio.AsyncResult
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """
        try:
            self.archive = self.dialog.save_finish(result)
            
            dialog = Adw.AlertDialog.new(
                heading=_("Confirm Export?"),
                body=_("Exporting your library will create an archive containing all your data. You can import this archive later to restore your library."),
            )
            dialog.add_response('cancel', C_('alert dialog action', '_Cancel'))
            dialog.add_response('export', C_('alert dialog action', '_Export'))
            dialog.set_default_response('export')
            dialog.set_close_response('cancel')
            dialog.set_response_appearance('export', Adw.ResponseAppearance.SUGGESTED)
            dialog.choose(self.props.active_window, None, self._on_export_alert_dialog_choose, None)

        except GLib.GError:
            logging.info("Export cancelled")

    def _on_export_alert_dialog_choose(self,
                                       source: GObject.Object | None,
                                       result: Gio.AsyncResult,
                                       user_data: object | None) -> None:
        """
        Callback for the export confirmation dialog.
        If the user confirms the export, the export process is started.

        Args:
            dialog (Adw.AlertDialog): the dialog that triggered the response
            response (int): the response code

        Returns:
            None
        """
        result = Adw.AlertDialog.choose_finish(source, result)

        if result == 'cancel':
            logging.info("Export cancelled")
            return
        
        BackgroundQueue.add(
            activity=BackgroundActivity(
                activity_type=ActivityType.ADD,
                title=C_('Background activity title', 'Exporting library'),
                task_function=self._export_content_from_db),
            on_done=self._on_export_done
        )
        
    def _export_content_from_db(self, activity: BackgroundActivity) -> bool:
        """
        Exports the library to the selected archive.

        Args:
            activity (BackgroundActivity): the calling activity

        Returns:
            bool: True if export succeeded, False otherwise
        """
        
        result = local.export_data(self.archive.get_path())
        if not result:
            activity.error()
            logging.info("Export failed")
        return result    
        
    def _on_export_done(self,
                     source: GObject.Object,
                     result: Gio.AsyncResult,
                     cancellable: Gio.Cancellable,
                     activity: BackgroundActivity):
        """Callback to complete async activity"""

        result = activity.activity_finish(result, activity)
        activity.end()
        if result:
            dialog = Adw.AlertDialog.new(
                heading=_("Export Completed"),
                body=_("The library has been exported successfully."),
            )
            dialog.set_close_response('ok')
            dialog.add_response('ok', C_('alert dialog action', '_OK'))
            dialog.set_default_response('ok')
            dialog.present(self.props.active_window)
            logging.info("Export done")
        else:
            dialog = Adw.AlertDialog.new(
                heading=_("Export failed"),
                body=_("An error occurred while exporting the library."),
            )
            dialog.set_close_response('ok')
            dialog.add_response('ok', C_('alert dialog action', '_OK'))
            dialog.set_default_response('ok')
            dialog.present(self.props.active_window)
            logging.info("Export failed")


    def do_import(self, new_state: None, source: Gtk.Widget) -> None:
        """
        Callback for the app.import action

        Args:
            new_state (None): the new state of the action
            source (Gtk.Widget): the widget that triggered the action

        Returns:
            None
        """

        logging.info('Import requested')
        logging.info('Opening file dialog to select import location')
        self.dialog = Gtk.FileDialog.new()
        self.dialog.set_modal(True)

        file_filter_store = Gio.ListStore.new(Gtk.FileFilter)
        file_filter = Gtk.FileFilter()
        file_filter.add_suffix("zip")
        file_filter_store.append(file_filter)

        self.dialog.set_filters(file_filter_store)
        self.dialog.open(self.props.active_window, None, self._on_file_open_complete, None)

    def _on_file_open_complete(self,
                               source: Gtk.Widget,
                               result: Gio.AsyncResult,
                               user_data: object | None) -> None:
        """
        Callback for the file dialog.
        Finishes the file selection and, if successfull, asks for confirmation

        Args:
            source (Gtk.Widget): caller widget
            result (Gio.AsyncResult): a Gio.AsyncResult
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        try:
            self.archive = self.dialog.open_finish(result)

            dialog = Adw.AlertDialog.new(
                heading=_("Confirm Import?"),
                body=_("Importing a library will merge it with the current library. This action cannot be undone and in case of conflicts, the new data will be kept."),
            )
            dialog.add_response('cancel', C_('alert dialog action', '_Cancel'))
            dialog.add_response('import', C_('alert dialog action', '_Import'))
            dialog.set_default_response('import')
            dialog.set_close_response('cancel')
            dialog.set_response_appearance('import', Adw.ResponseAppearance.SUGGESTED)
            dialog.choose(self.props.active_window, None, self._on_import_alert_dialog_choose, None)

        except GLib.GError:
            logging.info("Import cancelled")

    def _on_import_alert_dialog_choose(self,
                                       source: GObject.Object | None,
                                       result: Gio.AsyncResult,
                                       user_data: object | None) -> None:
        """
        Callback for the import confirmation dialog.
        If the user confirms the import, the import process is started.

        Args:
            dialog (Adw.AlertDialog): the dialog that triggered the response
            response (int): the response code

        Returns:
            None
        """
        result = Adw.AlertDialog.choose_finish(source, result)

        if result == 'cancel':
            logging.info("Import cancelled")
            return

        BackgroundQueue.add(
            activity=BackgroundActivity(
                activity_type=ActivityType.ADD,
                title=C_('Background activity title', 'Importing library'),
                task_function=self._import_content_to_db),
            on_done=self._on_import_done
        )


    def _import_content_to_db(self, activity: BackgroundActivity) -> bool:
        """
        Imports the library from the selected archive.

        Args:
            activity (BackgroundActivity): the calling activity

        Returns:
            bool: True if the import was successful, False otherwise
        """
        
        result = local.import_data(self.archive.get_path())
        if not result:
            activity.error()
            logging.info("Import failed")
        return result


    def _on_import_done(self,
                     source: GObject.Object,
                     result: Gio.AsyncResult,
                     cancellable: Gio.Cancellable,
                     activity: BackgroundActivity):
        """Callback to complete async activity"""

        result = activity.activity_finish(result, activity)
        activity.end()
        
        if result:
            self.props.active_window.activate_action('win.refresh')
            logging.info("Import completed successfully")
            dialog = Adw.AlertDialog.new(
                heading=_("Import Completed"),
                body=_("The library has been imported successfully."),
            )
            dialog.set_close_response('ok')
            dialog.add_response('ok', C_('alert dialog action', '_OK'))
            dialog.set_default_response('ok')
            dialog.present(self.props.active_window)
        else:
            dialog = Adw.AlertDialog.new(
                heading=_("Import failed"),
                body=_("Please check the selected archive and try again. Only archives created by Ticket Booth are supported."),
            )
            dialog.set_close_response('ok')
            dialog.add_response('ok', C_('alert dialog action', '_OK'))
            dialog.set_default_response('ok')
            dialog.present(self.props.active_window)

def main():
    """The application's entry point."""
    app = TicketboothApplication()
    return app.run([])
