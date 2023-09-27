# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gio, GLib, GObject, Gtk

from .. import shared  # type: ignore


@Gtk.Template(resource_path=shared.PREFIX + '/ui/widgets/image_selector.ui')
class ImageSelector(Adw.Bin):
    """
    This class represents the image selector and previewer with options to open a file and, if one is already opened,
    to delete the selection.

    Properties:
        content-fit (Gtk.ContentFit): content fit for the image

    Methods:
        set_file(file: Gio.File): sets the shown file
        get_uri(): gets the uri for the shown file

    Signals:
        None
    """

    __gtype_name__ = 'ImageSelector'

    content_fit = GObject.Property(type=Gtk.ContentFit, default=Gtk.ContentFit.FILL)
    shown_image = GObject.Property(type=str, default=f'resource://{shared.PREFIX}/blank_poster.jpg')
    blank_image = GObject.Property(type=str, default=f'resource://{shared.PREFIX}/blank_poster.jpg')

    _poster_picture = Gtk.Template.Child()
    _edit_btn = Gtk.Template.Child()
    _spinner = Gtk.Template.Child()
    _delete_revealer = Gtk.Template.Child()

    def __init__(self):
        super().__init__()

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data):
        self._poster_picture.set_file(Gio.File.new_for_uri(self.shown_image))

    @Gtk.Template.Callback('_on_edit_btn_clicked')
    def _on_edit_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for "clicked" signal.
        Setups and shows a file chooser dialog to choose a new image.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        self._edit_btn.set_sensitive(False)
        self._spinner.set_visible(True)

        file_filter_store = Gio.ListStore.new(Gtk.FileFilter)
        file_filter = Gtk.FileFilter()
        file_filter.add_pixbuf_formats()
        file_filter_store.append(file_filter)

        self.dialog = Gtk.FileDialog.new()
        self.dialog.set_modal(True)
        self.dialog.set_filters(file_filter_store)
        self.dialog.open(self.get_ancestor(Gtk.Window), None, self._on_file_open_complete, None)

    def _on_file_open_complete(self,
                               source: Gtk.Widget,
                               result: Gio.AsyncResult,
                               user_data: object | None) -> None:
        """
        Callback for the file dialog.
        Finishes the file selection and, if successfull, shows the new selected image.

        Args:
            source (Gtk.Widget): caller widget
            result (Gio.AsyncResult): a Gio.AsyncResult
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        try:
            poster_file = self.dialog.open_finish(result)
        except GLib.GError:
            poster_file = None

        if poster_file:
            self.shown_image = poster_file.get_uri()
            self._poster_picture.set_file(poster_file)
            self._delete_revealer.set_reveal_child(True)

        self._spinner.set_visible(False)
        self._edit_btn.set_sensitive(True)

    @Gtk.Template.Callback('_on_delete_btn_clicked')
    def _on_delete_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for "clicked" signal.
        Restores the blank image and hides the delete button.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        self.shown_image = self.blank_image
        self._poster_picture.set_file(Gio.File.new_for_uri(self.shown_image))
        self._delete_revealer.set_reveal_child(False)

    def set_blank_image(self, image_uri: str) -> None:
        """
        Sets the blank image and shows it.

        Args:
            image_uri (str): uri to use

        Returns:
            None
        """

        self.blank_image = image_uri
        self.shown_image = self.blank_image
        self._poster_picture.set_file(Gio.File.new_for_uri(self.shown_image))

    def set_image(self, image_uri: str) -> None:
        """
        Sets the image.

        Args:
            image_uri (str): uri to use

        Returns:
            None
        """

        self.shown_image = image_uri
        self._poster_picture.set_file(Gio.File.new_for_uri(self.shown_image))
        self._delete_revealer.set_reveal_child(True)

    def get_uri(self) -> str:
        """
        Returns the shown image uri.

        Args:
            None

        Returns:
            string with the uri
        """

        return self._poster_picture.get_file().get_uri()
