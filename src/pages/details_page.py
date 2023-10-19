# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
from datetime import date
from gettext import gettext as _
from gettext import ngettext
from gettext import pgettext as C_
from typing import List, Tuple

from gi.repository import Adw, Gio, GObject, Gtk
from PIL import Image, ImageStat

from .. import shared  # type: ignore
from ..background_queue import (ActivityType, BackgroundActivity,
                                BackgroundQueue)
from ..dialogs.add_manual_dialog import AddManualDialog
from ..models.movie_model import MovieModel
from ..models.season_model import SeasonModel
from ..models.series_model import SeriesModel
from ..providers.local_provider import LocalProvider as local
from ..providers.tmdb_provider import TMDBProvider as tmdb
from ..widgets.episode_row import EpisodeRow
from ..widgets.theme_switcher import ThemeSwitcher


@Gtk.Template(resource_path=shared.PREFIX + '/ui/pages/details_page.ui')
class DetailsView(Adw.NavigationPage):
    """
    Widget that represents the details view.

    Properties:
        content (MovieModel or SeriesModel): content associated to the information shown

    Methods:
        None

    Signals:
        deleted: emited when the user confirms the deletion of the content
        edited: emited when a user confirms the edits for manually added content
    """

    __gtype_name__ = 'DetailsView'

    content = GObject.Property(type=object)

    __gsignals__ = {
        'deleted': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'edited': (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    _view_stack = Gtk.Template.Child()
    _menu_btn = Gtk.Template.Child()
    _background_picture = Gtk.Template.Child()
    _poster_picture = Gtk.Template.Child()
    _title_lbl = Gtk.Template.Child()
    _tagline_lbl = Gtk.Template.Child()
    _genres_lbl = Gtk.Template.Child()
    _chip1_lbl = Gtk.Template.Child()
    _chip2_lbl = Gtk.Template.Child()
    _chip3_lbl = Gtk.Template.Child()
    _chip4_lbl = Gtk.Template.Child()
    _watched_btn = Gtk.Template.Child()
    _btn_content = Gtk.Template.Child()
    _edit_btn = Gtk.Template.Child()
    _update_btn = Gtk.Template.Child()
    _activate_notification_btn = Gtk.Template.Child()
    _notification_icon = Gtk.Template.Child()
    _description_box = Gtk.Template.Child()
    _overview_lbl = Gtk.Template.Child()
    _creator_box = Gtk.Template.Child()
    _creator_lbl = Gtk.Template.Child()
    _seasons_box = Gtk.Template.Child()
    _seasons_group = Gtk.Template.Child()
    _additional_info_box = Gtk.Template.Child()
    _flow_box = Gtk.Template.Child()
    _loading_lbl = Gtk.Template.Child()

    def __init__(self, content: MovieModel | SeriesModel):
        super().__init__()

        # Theme switcher (Adapted from https://gitlab.gnome.org/tijder/blueprintgtk/)
        self._menu_btn.get_popover().add_child(ThemeSwitcher(), 'themeswitcher')

        if type(content) is MovieModel:
            self.content = local.get_movie_by_id(content.id)
        else:
            self.content = local.get_series_by_id(content.id)
        logging.info(
            f'Loading info [{"movie" if type(content) is MovieModel else "TV Serie"}] {self.content.title}')

        self.set_title(self.content.title)  # type: ignore
        self._view_stack.set_visible_child_name('loading')
        self._populate_data()

    def _populate_data(self) -> None:
        """
        Populates the widgets with the available information.

        Args:
            None

        Returns:
            None
        """

        # Both movies and tv series
        if self.content.backdrop_path:  # type: ignore

            if not Adw.StyleManager.get_default().get_high_contrast():
                self._background_picture.set_file(Gio.File.new_for_uri(
                    self.content.backdrop_path))  # type: ignore
                # type: ignore
                with Image.open(self.content.backdrop_path[7:]) as image:
                    stat = ImageStat.Stat(image.convert('L'))

                    luminance = [
                        min((stat.mean[0] + stat.extrema[0][0]) / 510, 0.7),
                        max((stat.mean[0] + stat.extrema[0][1]) / 510, 0.3),
                    ]
                self._background_picture.set_opacity(1 - luminance[0]
                                                     if Adw.StyleManager.get_default().get_dark()
                                                     else luminance[1])

        self._poster_picture.set_file(Gio.File.new_for_uri(
            self.content.poster_path))  # type: ignore

        self._title_lbl.set_text(self.content.title)  # type: ignore

        if self.content.tagline:  # type: ignore
            self._tagline_lbl.set_visible(True)
            self._tagline_lbl.set_text(self.content.tagline)  # type: ignore

        if self.content.genres:  # type: ignore
            self._genres_lbl.set_visible(True)
            self._genres_lbl.set_label(
                ', '.join(self.content.genres))  # type: ignore

        if self.content.release_date:  # type: ignore
            self._chip1_lbl.set_visible(True)
            self._chip1_lbl.set_text(date.fromisoformat(
                self.content.release_date).strftime('%d %b. %Y'))  # type: ignore

        if self.content.next_air_date:  # type: ignore
            self._chip4_lbl.set_visible(True)
            self._chip4_lbl.set_text(date.fromisoformat(self.content.next_air_date).strftime('%d %b. %Y'))  # type: ignore        

        if self.content.manual:  # type: ignore
            self._edit_btn.set_visible(True)
        else:
            self._update_btn.set_visible(True)
            
        if not self.content.manual and self.content.in_production:
            self._notification_icon.set_visible(True)
            self._activate_notification_btn.set_visible(True)
            self._activate_notification_btn.set_active(local.get_notification_list_status(self.content.id))

        if self.content.overview:  # type: ignore
            self._description_box.set_visible(True)
            self._overview_lbl.set_label(self.content.overview)  # type: ignore

        # Movie specific
        if type(self.content) is MovieModel:
            self._watched_btn.set_visible(True)
            if self.content.watched:
                self._btn_content.set_label(_('Watched'))
                self._btn_content.set_icon_name('check-plain')
            else:
                self._btn_content.set_label(_('Mark as Watched'))
                self._btn_content.set_icon_name('watchlist')

            if self.content.runtime:
                self._chip2_lbl.set_visible(True)
                self._chip2_lbl.set_text(
                    self._format_runtime(self.content.runtime))

        # TV series specific
        if type(self.content) is SeriesModel:
            if self.content.seasons_number:
                self._chip2_lbl.set_visible(True)
                # TRANSLATORS: {num} is the total number of seasons
                self._chip2_lbl.set_text(ngettext('{num} Season'.format(num=self.content.seasons_number),
                                                  '{num} Seasons'.format(
                                                      num=self.content.seasons_number),
                                         self.content.seasons_number))

            if self.content.episodes_number:
                self._chip3_lbl.set_visible(True)
                # TRANSLATORS: {num} is the total number of episodes
                self._chip3_lbl.set_text(ngettext('{num} Episode'.format(num=self.content.episodes_number),
                                                  '{num} Episodes'.format(
                                                      num=self.content.episodes_number),
                                                  self.content.episodes_number))

            if self.content.created_by:
                self._creator_box.set_visible(True)
                self._creator_lbl.set_text(', '.join(self.content.created_by))

            self._seasons_box.set_visible(True)
            self._build_seasons_group()

        self._build_flow_box()
        self._view_stack.set_visible_child_name('filled')

    def _build_seasons_group(self) -> None:
        """
        Creates the widgets needed to show season and episodes metadata.

        Args:
            None

        Returns:
            None
        """

        list_box = self._seasons_group.get_first_child().get_last_child().get_first_child()
        list_box.remove_all()

        self._episode_rows = []
        for season in self.content.seasons:  # type: ignore
            season_row = Adw.ExpanderRow(title=season.title,
                                         subtitle=ngettext('{num} Episode'.format(num=season.episodes_number),
                                                           '{num} Episodes'.format(
                                                               num=season.episodes_number),
                                                           season.episodes_number))

            poster = Gtk.Picture(height_request=112,
                                 width_request=75,
                                 content_fit=Gtk.ContentFit.FILL,
                                 margin_top=12,
                                 margin_bottom=12)
            poster.add_css_class('still')
            poster.set_file(Gio.File.new_for_uri(season.poster_path))
            season_row.add_prefix(poster)

            button = Gtk.Button(valign=Gtk.Align.CENTER)
            btn_content = Adw.ButtonContent()

            if all(episode.watched for episode in season.episodes):
                btn_content.set_label(_('Watched'))
                btn_content.set_icon_name('check-plain')
            else:
                btn_content.set_label(_('Mark as Watched'))
                btn_content.set_icon_name('watchlist-symbolic')

            button.set_child(btn_content)
            season_row.add_suffix(button)

            tmp = []
            for episode in season.episodes:
                episode_row = EpisodeRow(episode)
                episode_row.connect(
                    'watched-clicked', self._on_episode_watch_clicked, (btn_content, season))
                season_row.add_row(episode_row)
                tmp.append(episode_row)

            self._seasons_group.add(season_row)
            self._episode_rows.append((season, tmp))

            button.connect('clicked', self._on_season_watched_clicked,
                           (btn_content, season, self._episode_rows))

    def _on_episode_watch_clicked(self,
                                  source: Gtk.Widget,
                                  data: Tuple[Adw.ButtonContent, SeasonModel]) -> None:
        """
        Callback for "watched-clicked" signal.
        Called after an episode is (un)marked as watched, checks and updates, if needed, the watched button for the corresponding season.

        Args:
            source (Gtk.Widget): caller widget
            data(tuple[Adw.ButtonContent, SeasonModel]): tuple with the Adw.ButtonContent to change and the SeasonModel
                parent of the changed episode

        Returns:
            None
        """

        self.content = local.get_series_by_id(self.content.id)  # type: ignore

        btn_content = data[0]
        season_idx = 0
        for idx, season in enumerate(self.content.seasons):  # type: ignore
            if season == data[1]:
                season_idx = idx

        if all(episode.watched for episode in self.content.seasons[season_idx].episodes):
            btn_content.set_label(_('Watched'))
            btn_content.set_icon_name('check-plain')
        else:
            btn_content.set_label(_('Mark as Watched'))
            btn_content.set_icon_name('watchlist')

        # Update season status
        local.mark_watched_series(self.content.id, all(
            episode.watched for season in self.content.seasons for episode in season.episodes))  # type: ignore
        self.activate_action('win.refresh', None)

    def _on_season_watched_clicked(self,
                                   source: Gtk.Widget,
                                   data: Tuple[Adw.ButtonContent, SeasonModel, List[Tuple[SeasonModel, List[EpisodeRow]]]]) -> None:
        """
        Callback for "clicked" signal.
        Marks a whole season as (un)watched, making changes in the db and updating the ui.

        Args:
            source (Gtk.Widget): caller widget
            data (Tuple[Adw.ButtonContent, SeasonModel, List[Tuple[SeasonModel, List[EpisodeRow]]]]): tuple with the
                Adw.ButtonContent to change, the SeasonModel of the modified season, and a list of tuples of all
                SeasonModels and associated EpisodeRows.

        Returns:
            None
        """

        self.content = local.get_series_by_id(self.content.id)  # type: ignore

        btn_content = data[0]
        season_idx = 0
        for idx, season in enumerate(self.content.seasons):  # type: ignore
            if season == data[1]:
                season_idx = idx

        episode_rows = []
        for item in data[2]:
            if item[0] == self.content.seasons[season_idx]:  # type: ignore
                episode_rows = item[1]

        # Make changes in db
        # type: ignore
        for episode in self.content.seasons[season_idx].episodes:
            local.mark_watched_episode(episode.id, not all(
                episode.watched for episode in self.content.seasons[season_idx].episodes))  # type: ignore

        # Update episode rows
        for episode_row in episode_rows:
            episode_row.set_watched_btn(
                not all(episode.watched for episode in self.content.seasons[season_idx].episodes))  # type: ignore

        # Update season expander
        if not all(episode.watched for episode in self.content.seasons[season_idx].episodes):
            btn_content.set_label(_('Watched'))
            btn_content.set_icon_name('check-plain')
        else:
            btn_content.set_label(_('Mark as Watched'))
            btn_content.set_icon_name('watchlist')

        # Update season status
        local.mark_watched_series(self.content.id, not all(  # type: ignore
            episode.watched for season in self.content.seasons for episode in season.episodes))  # type: ignore
        self.activate_action('win.refresh', None)

    def _build_flow_box(self) -> None:
        """
        Adds the available metadata to the 'additional information' section.

        Args:
            None

        Returns:
            None
        """

        if self._flow_box.get_child_at_index(0):
            return

        # Both movies and tv series
        if self.content.status:  # type: ignore
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            label = Gtk.Label(label=_('Status'))
            label.add_css_class('heading')
            box.append(label)
            box.append(Gtk.Label(label=self.content.status))  # type: ignore
            self._flow_box.append(box)

        if self.content.original_language and self.content.original_language.iso_name != 'xx':  # type: ignore
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            label = Gtk.Label(label=_('Original Language'))
            label.add_css_class('heading')
            box.append(label)
            # type: ignore
            box.append(Gtk.Label(label=self.content.original_language.name))
            self._flow_box.append(box)

        if self.content.original_title:  # type: ignore
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            label = Gtk.Label(label=_('Original Title'))
            label.add_css_class('heading')
            box.append(label)
            # type: ignore
            box.append(Gtk.Label(label=self.content.original_title))
            self._flow_box.append(box)

        # Movie specific
        if type(self.content) is MovieModel:
            if self.content.budget:
                box = Gtk.Box(
                    orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                label = Gtk.Label(label=_('Budget'))
                label.add_css_class('heading')
                box.append(label)
                box.append(Gtk.Label(label='US$ {budget:0.0f}'.format(
                    budget=self.content.budget)))
                self._flow_box.append(box)

            if self.content.revenue:
                box = Gtk.Box(
                    orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                label = Gtk.Label(label=_('Revenue'))
                label.add_css_class('heading')
                box.append(label)
                box.append(Gtk.Label(label='US$ {revenue:0.0f}'.format(
                    revenue=self.content.revenue)))
                self._flow_box.append(box)

        # TV series specific
        if type(self.content) is SeriesModel:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            label = Gtk.Label(label=_('In Production'))
            label.add_css_class('heading')
            box.append(label)
            box.append(Gtk.Label(label=_('Yes')
                       if self.content.in_production else _('No')))
            self._flow_box.append(box)

        if self.content.id and self.content.manual == False:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            label = Gtk.Label(label=_('TMDB ID'))
            label.add_css_class('heading')
            box.append(label)
            url_str = '<a href="https://www.themoviedb.org/{category}/{id}" title="TMDB Webpage"> {id} </a>' \
                .format(category = ("tv") if type(self.content) is SeriesModel else ("movie"), id = self.content.id)
            box.append(Gtk.Label(label=url_str, use_markup = True))
            self._flow_box.append(box)

        if self._flow_box.get_child_at_index(0) is None:
            self._additional_info_box.set_visible(False)

    def _format_runtime(self, runtime: str) -> str:
        """
        Formats the runtime in hours and minutes.

        Args:
            runtime (str): runtime in minutes

        Returns:
            formatted duration string in hours and minutes
        """

        h, m = divmod(int(runtime), 60)

        if h > 0:
            # TRANSLATORS: {h} and {m} are the runtime hours and minutes respectively
            return _('{h}h {m}min').format(h=h, m=m)
        else:
            # TRANSLATORS: {m} is the runtime minutes
            return _('{m}min').format(m=m)

    @Gtk.Template.Callback('_on_watched_btn_clicked')
    def _on_watched_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for the "clicked" signal.
        Updates the watched flag for the content in the db and changes the button text accordingly.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        if type(self.content) is MovieModel:
            local.mark_watched_movie(self.content.id, not self.content.watched)

        self.content.watched = not self.content.watched  # type: ignore

        if self.content.watched:
            self._btn_content.set_label(_('Watched'))
            self._btn_content.set_icon_name('check-plain')
        else:
            self._btn_content.set_label(_('Mark as Watched'))
            self._btn_content.set_icon_name('watchlist')

        self.activate_action('win.refresh', None)

    @Gtk.Template.Callback('_on_edit_btn_clicked')
    def _on_edit_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for the "clicked" signal.
        Opens the edit window to change the metadata of the content. Available only for manually added content.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        logging.info(
            f'Editing [{"movie" if type(self.content) is MovieModel else "TV Serie"}] {self.content.title}')

        dialog = AddManualDialog(self.get_ancestor(
            Gtk.Window), True, self.content)
        dialog.connect('edit-saved', self._on_edit_saved)
        dialog.present()

    def _on_edit_saved(self, source: Gtk.Widget, content: MovieModel | SeriesModel) -> None:
        """
        Callback for "edit-saved" signal.
        Replaces the navigation stack with an updated top page resulting in a content refresh.

        Args:
            source (Gtk.Widget): caller widget
            content (MovieModel or SeriesModel): updated content to show

        Returns:
            None
        """

        root_page = self.get_ancestor(
            Adw.NavigationView).get_previous_page(self)
        self.get_ancestor(Adw.NavigationView).replace(
            [root_page, DetailsView(content)])

    @Gtk.Template.Callback('_on_update_btn_clicked')
    def _on_update_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for "clicked" signal.
        Adds a background activity to start a manual update.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        self._view_stack.set_visible_child_name('loading')

        # TRANSLATORS: {title} is the showed content's title
        self._loading_lbl.set_label(_('Updating {title}').format(
            title=self.content.title))  # type: ignore

        BackgroundQueue.add(
            activity=BackgroundActivity(
                activity_type=ActivityType.UPDATE,
                # TRANSLATORS: {title} is the content's title
                title=_('Update {title}').format(title=self.content.title),
                task_function=self._update),
            on_done=self._on_update_done)

    @Gtk.Template.Callback('_activate_notification_btn_toggled')
    def _activate_notification_btn_toggled(self, user_data: object | None) -> None:
        """
        Callback for "clicked" signal.
        Adds the series to the notification list
        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """
        
        local.set_notification_list_status(self.content.id, self._activate_notification_btn.get_active())

        # TODO Trigger if a soon_release should be set

        #if we remove the series from the notification_list then remove the new/soon_release flags
        if not self._activate_notification_btn.get_active():
            local.set_new_release_status(self.content.id, False)
            local.set_soon_release_status(self.content.id, False)


    def _update(self, activity: BackgroundActivity) -> None:
        """
        Fetches updated information and updates the stored copy. Additionally it handles ui updates.

        Args:
            activity (BackgroundActivity): the calling activity

        Returns:
            None
        """

        if type(self.content) is MovieModel:
            self.new_content = MovieModel(tmdb.get_movie(self.content.id))
            local.update_movie(old=self.content, new=self.new_content)
            self.new_content = local.get_movie_by_id(self.content.id)
        else:
            self.new_content = SeriesModel(tmdb.get_serie(self.content.id))
            local.update_series(old=self.content, new=self.new_content)
            self.new_content = local.get_series_by_id(self.content.id)
            

    def _on_update_done(self,
                        source: GObject.Object,
                        result: Gio.AsyncResult,
                        cancellable: Gio.Cancellable,
                        activity: BackgroundActivity):
        """Callback to complete async activity"""

        root_page = self.get_ancestor(
            Adw.NavigationView).get_previous_page(self)
        self.get_ancestor(Adw.NavigationView).replace(
            [root_page, DetailsView(self.new_content)])
        self._loading_lbl.set_label(_('Loading Metadata…'))
        self._view_stack.set_visible_child_name('filled')
        activity.end()

    @Gtk.Template.Callback('_on_delete_btn_clicked')
    def _on_delete_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for the "clicked" signal.
        Asks the user for a confirmation after a delete request.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        logging.debug('Show delete dialog')
        dialog = Adw.MessageDialog.new(self.get_ancestor(Adw.ApplicationWindow),  # TRANSLATORS: {title} is the content's title
                                       C_('message dialog heading', 'Delete {title}?').format(
                                           title=self.content.title),
                                       C_('message dialog body', 'This title will be deleted from your notification list.'))
        dialog.add_response('cancel', C_('message dialog action', '_Cancel'))
        dialog.add_response('delete', C_('message dialog action', '_Delete'))
        dialog.set_response_appearance(
            'delete', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.choose(None, self._on_message_dialog_choose, None)

    def _on_message_dialog_choose(self, source: GObject.Object | None, result: Gio.AsyncResult, user_data: object | None) -> None:
        """
        Callback for the message dialog.
        Finishes the async operation and retrieves the user response. If the later is positive, adds a background activity to delete the content.

        Args:
            source (Gtk.Widget): object that started the async operation
            result (Gio.AsyncResult): a Gio.AsyncResult
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        result = Adw.MessageDialog.choose_finish(source, result)
        if result == 'cancel':
            logging.debug('Delete dialog: cancel, aborting')
            return

        self.get_ancestor(Adw.NavigationView).pop()
        logging.debug(f'Delete dialog: confim, delete {self.content.title}')
        BackgroundQueue.add(
            activity=BackgroundActivity(
                activity_type=ActivityType.REMOVE,
                # TRANSLATORS: {title} is the content's title
                title=_('Delete {title}').format(title=self.content.title),
                task_function=self._delete),
            on_done=self._on_delete_done)

    def _delete(self, activity: BackgroundActivity) -> None:
        """
        Deletes the content from the db.

        Args:
            activity (BackgroundActivity): the calling activity

        Returns:
            None
        """

        if type(self.content) is MovieModel:
            local.delete_movie(self.content.id)
        else:
            local.delete_series(self.content.id)  # type: ignore

    def _on_delete_done(self,
                        source: GObject.Object,
                        result: Gio.AsyncResult,
                        cancellable: Gio.Cancellable,
                        activity: BackgroundActivity):
        """Callback to complete async activity"""

        self.emit('deleted')
        activity.end()
