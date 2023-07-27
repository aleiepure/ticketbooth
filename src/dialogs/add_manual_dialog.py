# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, GObject, Gtk

from .. import shared  # type: ignore


@Gtk.Template(resource_path=shared.PREFIX + '/ui/dialogs/add_manual.ui')
class AddManualDialog(Adw.Window):
    """
    This class rappresents the window to manually add content to the db.
    Not finished yet.

    Properties:
        None

    Methods:
        None

    Signals:
        None
    """

    __gtype_name__ = 'AddManualDialog'

    _done_btn = Gtk.Template.Child()

    _title_entry_has_text = False
    _year_entry_has_text = False

    def __init__(self, parent: Gtk.Window):
        super().__init__()
        self.set_transient_for(parent)

    @Gtk.Template.Callback('_on_done_btn_clicked')
    def _on_done_btn_clicked(self, user_data: GObject.GPointer):
        print('done clicked')

    @Gtk.Template.Callback('_on_edit_btn_clicked')
    def _on_edit_btn_clicked(self, user_data: GObject.GPointer):
        print('edit clicked')

    @Gtk.Template.Callback('_on_delete_btn_clicked')
    def _on_delete_btn_clicked(self, user_data: GObject.GPointer):
        print('delete clicked')

    @Gtk.Template.Callback('_on_title_entry_changed')
    def _on_title_entry_changed(self, source: GObject.GPointer):
        if source.get_text():
            self._title_entry_has_text = True
        else:
            self._title_entry_has_text = False
        self._enable_done_btn()

    @Gtk.Template.Callback('_on_year_entry_changed')
    def _on_year_entry_changed(self, source: GObject.GPointer):
        if source.get_text():
            self._year_entry_has_text = True
        else:
            self._year_entry_has_text = False
        self._enable_done_btn()

    def _enable_done_btn(self):
        self._done_btn.set_sensitive(self._title_entry_has_text and self._year_entry_has_text)
