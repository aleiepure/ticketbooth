# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from gettext import gettext as _
from typing import Callable

from gi.repository import Adw, GObject, Gtk, GLib

import src.providers.local_provider as local

from .. import shared  # type: ignore
from ..models.movie_model import MovieModel
from ..models.series_model import SeriesModel
from ..pages.details_page import DetailsView
from ..widgets.poster_button import PosterButton


@Gtk.Template(resource_path=shared.PREFIX + '/ui/views/content_view.ui')
class ContentView(Adw.Bin):
    """
    This class represents the content grid view.

    Properties:
        None

    Methods:
        refresh(): Causes the view to update its contents

    Signals:
        None
    """

    __gtype_name__ = 'ContentView'

    movie_view = GObject.Property(type=bool, default=True)
    icon_name = GObject.Property(type=str, default='movies')

    _stack = Gtk.Template.Child()
    _updating_status_lbl = Gtk.Template.Child()
    _title_lbl = Gtk.Template.Child()
    _scrolled_window = Gtk.Template.Child()
    _flow_box = Gtk.Template.Child()
    _full_box = Gtk.Template.Child()
    _separated_box = Gtk.Template.Child()
    _unwatched_box = Gtk.Template.Child()
    _unwatched_flow_box = Gtk.Template.Child()
    _watched_box = Gtk.Template.Child()
    _watched_flow_box = Gtk.Template.Child()

    def __init__(self, movie_view: bool):
        super().__init__()
        self.movie_view = movie_view
        self.icon_name = 'movies' if self.movie_view else 'series'

        self._stack.set_visible_child_name('loading')

        # Chunked loading state
        self._content_loaded = False
        self._pending_items = []
        self._load_index = 0

        self._set_sorting_function()
        self._set_filter_function()

        shared.schema.connect('changed::view-sorting', self._on_sort_changed)
        shared.schema.connect('changed::separate-watched',
                              self._on_separate_watched_changed)
        shared.schema.connect('changed::hide-watched',
                              self._on_hide_watched_changed)
        shared.schema.connect('changed::search-query',
                              self._on_search_enabled_changed)

    @Gtk.Template.Callback()
    def _on_map(self, user_data: object | None) -> None:
        """
        Callback for the "map" signal.
        Starts chunked content loading and restores scroll position.
        """
        
        # Start chunked loading on first map
        if not self._content_loaded:
            self._content_loaded = True
            GLib.idle_add(self._start_chunked_load)
        
        # Restore scroll position
        if hasattr(self, '_saved_scroll_value'):
            vadjustment = self._scrolled_window.get_vadjustment()
            GLib.idle_add(lambda: vadjustment.set_value(self._saved_scroll_value))

    def _on_sort_changed(self, pspec: GObject.ParamSpec, user_data: object | None) -> None:
        """
        Callback for the "changed" signal.
        Calls the function to set the sorting function on the FlowBox.

        Args:
            pspec (GObject.ParamSpec): pspec of the changed property
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        self._set_sorting_function()

    def _on_separate_watched_changed(self, pspec: GObject.ParamSpec, user_data: object | None) -> None:
        """
        Callback for the "changed" signal.


        Args:
            pspec (GObject.ParamSpec): pspec of the changed property
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        self.refresh_view()

    def _on_hide_watched_changed(self, pspec: GObject.ParamSpec, user_data: object | None) -> None:
        """
        Callback for the "changed" signal.


        Args:
            pspec (GObject.ParamSpec): pspec of the changed property
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        self._set_filter_function()

    # ══════════════════════════════════════════════════════════════════════════
    # CHUNKED LOADING - Prevents UI freeze with large datasets
    # ══════════════════════════════════════════════════════════════════════════
    
    CHUNK_SIZE = 25  # Widgets per chunk
    CHUNK_DELAY_MS = 8  # ~120 FPS - UI stays responsive
    
    def _start_chunked_load(self) -> bool:
        """
        Fetches all content and starts chunked widget creation.
        Called via GLib.idle_add from _on_map.
        """
        logging.info(f"[ContentView] Starting chunked load for {'movies' if self.movie_view else 'series'}")
        
        # Fetch all data (this is fast - just DB read + object creation)
        if self.movie_view:
            self._pending_items = local.LocalProvider.get_all_movies() or []
        else:
            self._pending_items = local.LocalProvider.get_all_series() or []
        
        if not self._pending_items:
            self._stack.set_visible_child_name('empty')
            logging.info("[ContentView] No content found")
            return False
        
        logging.info(f"[ContentView] Loaded {len(self._pending_items)} items, starting widget creation")
        
        self._load_index = 0
        # Start chunked widget creation
        GLib.timeout_add(self.CHUNK_DELAY_MS, self._load_next_chunk)
        
        return False  # Don't repeat idle_add
    
    def _load_next_chunk(self) -> bool:
        """
        Creates CHUNK_SIZE widgets and adds them to FlowBox.
        Returns True to continue, False when done.
        """
        if self._load_index >= len(self._pending_items):
            # All widgets created
            self._finalize_chunked_load()
            return False
        
        # Show filled view on first chunk
        if self._load_index == 0:
            self._stack.set_visible_child_name('filled')
        
        # Process one chunk
        end_index = min(self._load_index + self.CHUNK_SIZE, len(self._pending_items))
        
        for i in range(self._load_index, end_index):
            item = self._pending_items[i]
            btn = PosterButton(content=item)
            btn.connect('clicked', self._on_clicked)
            
            if not shared.schema.get_boolean('search-enabled') and shared.schema.get_boolean('separate-watched'):
                if item.watched:
                    self._watched_flow_box.insert(btn, -1)
                else:
                    self._unwatched_flow_box.insert(btn, -1)
            else:
                self._flow_box.insert(btn, -1)
        
        self._load_index = end_index
        return True  # Continue with next chunk
    
    def _finalize_chunked_load(self) -> None:
        """
        Called when all widgets are created.
        Sets up FlowBox visibility and focusability.
        """
        logging.info(f"[ContentView] Chunked load complete: {len(self._pending_items)} widgets created")
        
        # Disable focusable on all children
        idx = 0
        while self._flow_box.get_child_at_index(idx):
            self._flow_box.get_child_at_index(idx).set_focusable(False)
            idx += 1

        idx = 0
        while self._watched_flow_box.get_child_at_index(idx):
            self._watched_flow_box.get_child_at_index(idx).set_focusable(False)
            idx += 1

        idx = 0
        while self._unwatched_flow_box.get_child_at_index(idx):
            self._unwatched_flow_box.get_child_at_index(idx).set_focusable(False)
            idx += 1

        # Set box visibility
        self._full_box.set_visible(False)
        self._separated_box.set_visible(False)
        self._unwatched_box.set_visible(False)
        self._watched_box.set_visible(False)

        if not shared.schema.get_boolean('search-enabled') and shared.schema.get_boolean('separate-watched'):
            self._separated_box.set_visible(True)
            if self._watched_flow_box.get_child_at_index(0) is not None:
                self._watched_box.set_visible(True)
            if self._unwatched_flow_box.get_child_at_index(0) is not None:
                self._unwatched_box.set_visible(True)
        else:
            self._full_box.set_visible(True)
        
        # Clear pending items to free memory
        self._pending_items = []

    def _load_content(self, movie_view: bool) -> None:
        """
        For each title currently in the db, creates a PosterButton and adds it to the FlowBox.

        Args:
            movie_view (bool): if true it will load movies, otherwise it will load series

        Returns:
            None
        """

        # self._stack.set_visible_child_name('loading')
        if movie_view:
            content = local.LocalProvider.get_all_movies()
        else:
            content = local.LocalProvider.get_all_series()

        if not content:
            self._stack.set_visible_child_name('empty')
            return
        else:
            self._stack.set_visible_child_name('filled')

        for item in content:
            logging.debug(
                f'Created poster button for [{"movie" if self.movie_view else "TV series"}] {item.title}')
            btn = PosterButton(content=item)
            btn.connect('clicked', self._on_clicked)
            if not shared.schema.get_boolean('search-enabled') and shared.schema.get_boolean('separate-watched'):
                if item.watched:
                    self._watched_flow_box.insert(btn, -1)
                else:
                    self._unwatched_flow_box.insert(btn, -1)
            else:
                self._flow_box.insert(btn, -1)

        idx = 0
        while self._flow_box.get_child_at_index(idx):
            self._flow_box.get_child_at_index(idx).set_focusable(False)
            idx += 1

        idx = 0
        while self._watched_flow_box.get_child_at_index(idx):
            self._watched_flow_box.get_child_at_index(idx).set_focusable(False)
            idx += 1

        idx = 0
        while self._watched_flow_box.get_child_at_index(idx):
            self._watched_flow_box.get_child_at_index(idx).set_focusable(False)
            idx += 1

        self._full_box.set_visible(False)
        self._separated_box.set_visible(False)
        self._unwatched_box.set_visible(False)
        self._watched_box.set_visible(False)

        if not shared.schema.get_boolean('search-enabled') and shared.schema.get_boolean('separate-watched'):
            self._separated_box.set_visible(True)
            if self._watched_flow_box.get_child_at_index(0) is not None:
                self._watched_box.set_visible(True)
            if self._unwatched_flow_box.get_child_at_index(0) is not None:
                self._unwatched_box.set_visible(True)
        else:
            self._full_box.set_visible(True)

        # self._stack.set_visible_child_name('filled')

    def refresh_view(self) -> None:
        """
        Causes the view to refresh its contents by replacing the content of the FlowBox.

        Args:
            None

        Returns:
            None
        """

        # self._stack.set_visible_child_name('loading')

        self._flow_box.remove_all()
        self._watched_flow_box.remove_all()
        self._unwatched_flow_box.remove_all()

        self._load_content(self.movie_view)

    def _on_clicked(self, source: Gtk.Widget, content: MovieModel | SeriesModel) -> None:
        """
        Callback for the "clicked" signal.
        Opens the details view for the selected content.

        Args:
            source (Gtk.Widget): widget that emited the signal
            movie (MovieModel): associated movie

        Returns:
            None
        """

        # Create the details page
        logging.info(
            f'Clicked on [{"movie" if self.movie_view else "TV series"}] {content.title}')
        page = DetailsView(content, self)
        page.connect('deleted', lambda *args: self.refresh_view())
        
        # Preserve the scroll position
        vadjustment = self._scrolled_window.get_vadjustment()
        self._saved_scroll_value = vadjustment.get_value()
        
        # Push the details page onto the navigation stack
        self.get_ancestor(Adw.NavigationView).push(page)

    def _set_sorting_function(self) -> None:
        """
        Based on the current setting, sets the sorting function of the FlowBox.

        Args:
            None

        Returns;
            None
        """

        def get_sort_func(key: str) -> Callable | None:
            match key:
                case 'az':
                    return lambda child1, child2, user_data: (
                        (child1.get_child().title > child2.get_child().title) -
                        (child1.get_child().title < child2.get_child().title)
                    )
                case 'za':
                    return lambda child1, child2, user_data: (
                        (child1.get_child().title < child2.get_child().title) -
                        (child1.get_child().title > child2.get_child().title)
                    )
                case 'added-date-new':
                    return lambda child1, child2, user_data: (
                        (child1.get_child().content.add_date < child2.get_child().content.add_date) -
                        (child1.get_child().content.add_date >
                        child2.get_child().content.add_date)
                    )
                case 'added-date-old':
                    return lambda child1, child2, user_data: (
                        (child1.get_child().content.add_date > child2.get_child().content.add_date) -
                        (child1.get_child().content.add_date <
                        child2.get_child().content.add_date)
                    )
                case 'released-date-new':
                    return lambda child1, child2, user_data: (
                        (child1.get_child().content.release_date < child2.get_child().content.release_date) -
                        (child1.get_child().content.release_date >
                        child2.get_child().content.release_date)
                    )
                case 'released-date-old':
                    return lambda child1, child2, user_data: (
                        (child1.get_child().content.release_date > child2.get_child().content.release_date) -
                        (child1.get_child().content.release_date <
                        child2.get_child().content.release_date)
                    )
            return None
        
        sort_key = shared.schema.get_string('view-sorting')
        sort_func = get_sort_func(sort_key)

        if not shared.schema.get_boolean('search-enabled') and shared.schema.get_boolean('separate-watched'):
            # Apply sorting to both watched and unwatched flow boxes
            if sort_func:
                self._watched_flow_box.set_sort_func(sort_func, None)
                self._unwatched_flow_box.set_sort_func(sort_func, None)
                self._watched_flow_box.invalidate_sort()
                self._unwatched_flow_box.invalidate_sort()
        else:
            # Apply sorting to the main flow box
            if sort_func:
                self._flow_box.set_sort_func(sort_func, None)
                self._flow_box.invalidate_sort()

    def _set_filter_function(self) -> None:
        """
        Based on the current setting, sets the filter function of the FlowBox.

        Args:
            None

        Returns;
            None
        """
                    
        if shared.schema.get_boolean('search-enabled'):
            if shared.schema.get_string('search-mode') == 'title':
                self._flow_box.set_filter_func(
                    lambda child,
                    user_data: (
                        shared.schema.get_string(
                            'search-query').lower() in child.get_child().content.title.lower()
                    ),
                    None)
            elif shared.schema.get_string('search-mode') == 'genre':
                self._flow_box.set_filter_func(
                    lambda child, user_data: (
                        any(
                            shared.schema.get_string(
                                'search-query').title() in genre
                            for genre in child.get_child().content.genres)
                    ),
                    None)
            elif shared.schema.get_string('search-mode') == 'overview':
                self._flow_box.set_filter_func(
                    lambda child, user_data: (
                        shared.schema.get_string(
                            'search-query').lower() in child.get_child().content.overview.lower()
                    ),
                    None)
            elif shared.schema.get_string('search-mode') == 'notes':
                self._flow_box.set_filter_func(
                    lambda child, user_data: (
                        shared.schema.get_string(
                            'search-query').lower() in child.get_child().content.notes.lower()
                    ),
                    None)
            elif shared.schema.get_string('search-mode') == 'tmdb-id':
                self._flow_box.set_filter_func(
                    lambda child, user_data: (
                        shared.schema.get_string(
                            'search-query').lower() in child.get_child().content.id.lower()
                    ),
                    None)
            self._flow_box.invalidate_filter()
            return

        if shared.schema.get_boolean('hide-watched'):
            self._flow_box.set_filter_func(lambda child, user_data: (
                not child.get_child().content.watched), None)
            self._flow_box.invalidate_filter()
            return

        self._flow_box.set_filter_func(lambda child, user_data: True, None)
        self._flow_box.invalidate_filter()

    def _on_search_enabled_changed(self, pspec: GObject.ParamSpec, user_data: object | None) -> None:
        """
        Callback for the "changed" signal.
        Refreshes the view when the search is enabled or disabled.

        Args:
            pspec (GObject.ParamSpec): pspec of the changed property
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        self._title_lbl.set_label(_("Search results") if shared.schema.get_boolean(
            'search-enabled') else _("Your Watchlist"))

        # =============================================================================
        # PERFORMANCE FIX
        # =============================================================================
        # OLD CODE (REMOVED):
        # self.refresh_view()
        #
        # WHY WAS IT REMOVED?
        # - refresh_view() was called on every typed character
        # - This recreated all SeriesModels
        # - 1453 content × every character = too many object creations!
        # - Just updating the filter function is sufficient
        # =============================================================================

        self._set_filter_function()
