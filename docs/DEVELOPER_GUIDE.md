# Ticketbooth Developer Guide

> Architecture documentation for contributors and maintainers.

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [ContentGridView - Virtualization](#contentgridview---virtualization)
3. [Dashboard Mode](#dashboard-mode)
4. [Navigation Patterns](#navigation-patterns)
5. [Signal Patterns](#signal-patterns)
6. [Performance Tips](#performance-tips)

---

## Architecture Overview

Ticketbooth uses **GTK4** and **Libadwaita 1.6** for its UI layer with **SQLite** for persistence.

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| `ContentGridView` | `src/views/content_grid_view.py` | Virtualized grid display |
| `MainView` | `src/views/main_view.py` | Tab orchestration + navigation |
| `LocalProvider` | `src/providers/local_provider.py` | Database queries |
| `DetailsView` | `src/pages/details_page.py` | Item detail display |

---

## ContentGridView - Virtualization

The `ContentGridView` uses **widget recycling** to handle 1400+ items efficiently.

### How It Works

```
┌─────────────────────────────────────┐
│ Gio.ListStore (holds ALL models)    │
│ [Model₀, Model₁, ... Model₁₄₀₀]     │
└─────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ Gtk.SignalListItemFactory           │
│ Creates ~25 PosterButton widgets    │
│ Recycles them during scroll         │
└─────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ Gtk.GridView (visible area only)    │
│ [Widget₀][Widget₁]...[Widget₂₄]     │
└─────────────────────────────────────┘
```

### Factory Lifecycle

```python
# 1. SETUP (once per visible slot)
def _on_factory_setup(self, factory, list_item):
    btn = PosterButton(content=None)  # Empty shell
    list_item.set_child(btn)

# 2. BIND (each time new data enters viewport)
def _on_factory_bind(self, factory, list_item):
    btn = list_item.get_child()
    model = list_item.get_item()
    btn.update_content(model)
    btn.connect('clicked', self._on_child_clicked)

# 3. UNBIND (before recycling)
def _on_factory_unbind(self, factory, list_item):
    btn = list_item.get_child()
    btn.disconnect_by_func(self._on_child_clicked)  # CRITICAL!
    btn.reset_state()
```

> ⚠️ **Memory Leak Warning:** Always disconnect signals in `unbind` to prevent handler accumulation.

---

## Dashboard Mode

`dashboard_mode=True` limits initial fetch to 10 items for fast startup.

### Usage

```python
# Dashboard view (10 items, show "Show All" button)
dash = ContentGridView(movie_view=True, dashboard_mode=True)

# Full view (all items, no button)
full = ContentGridView(movie_view=True, dashboard_mode=False)
```

### Backend Support

```python
# LocalProvider methods (src/providers/local_provider.py)
LocalProvider.get_recent_movies_raw(limit=10)  # Latest 10
LocalProvider.get_total_movie_count()          # Total count for button
```

---

## Navigation Patterns

### Adw.NavigationView Requirements

`Adw.NavigationView` **only accepts `Adw.NavigationPage`** children.

```python
# ❌ WRONG - will not work properly
nav_view.push(content_grid_view)

# ✅ CORRECT - wrap in NavigationPage
page = Adw.NavigationPage(child=content_grid_view, title="Movies")
nav_view.push(page)
```

### Signal Flow for "Show All"

```
ContentGridView                 MainView
     │                              │
     │ emit('show-all')             │
     │ ─────────────────────────▶   │
     │                              │ create full_view
     │                              │ wrap in NavigationPage
     │                              │ nav_view.push(page)
     │                              │
```

---

## Signal Patterns

### Defining Custom Signals

```python
class ContentGridView(Adw.Bin):
    __gsignals__ = {
        'show-all': (GObject.SignalFlags.RUN_FIRST, None, (object,))
    }
    
    def _emit_show_all(self):
        self.emit('show-all', None)
```

### Connecting Signals

```python
# In MainView
dash = ContentGridView(movie_view=True, dashboard_mode=True)
dash.connect('show-all', self._on_show_all_movies)

def _on_show_all_movies(self, view, data=None):
    # 'data' parameter receives the object from signal tuple
    pass
```

---

## Performance Tips

### 1. Chunked Loading

Load items in chunks to keep UI responsive during large data sets.

```python
CHUNK_SIZE = 20
self._load_source_id = GLib.timeout_add(8, self._add_models_chunk)

def _add_models_chunk(self):
    chunk = self._pending_models[self._load_index:self._load_index + CHUNK_SIZE]
    self._store.splice(self._load_index, 0, chunk)
    self._load_index += CHUNK_SIZE
    return self._load_index < len(self._pending_models)
```

### 2. Debounce Clicks

Prevent double-navigation from rapid clicks.

```python
current_time = GLib.get_monotonic_time()
if (current_time - self._last_click_time) < 1_000_000:  # 1 second
    return
self._last_click_time = current_time
```

### 3. Cancel Pending Loads

Cancel async operations before clearing stores.

```python
def refresh_view(self):
    if self._load_source_id:
        GLib.source_remove(self._load_source_id)
        self._load_source_id = None
    self._store.remove_all()
```

### 4. Disable Kinetic Scrolling

Reduces jitter with GridView virtualization.

```python
Gtk.ScrolledWindow(kinetic_scrolling=False)
```

---

## See Also

- [GTK4 GridView Docs](https://docs.gtk.org/gtk4/class.GridView.html)
- [Adw.NavigationView](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/class.NavigationView.html)
