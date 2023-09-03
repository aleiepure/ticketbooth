# Contributing
Ticket Booth is a Linux app built with Python using the GTK4 toolkit and libadwaita. The only officially supported packaging format is Flatpak.


## Code
When contributing to the source code, use the same style and conventions present in the files already in the repo. \
All contributions are and will always be welcome.\
If you have an idea, feel free to create an issue and let's discuss it. You can also fork the repo, make your changes, and submit a pull request to change the code yourself.

## Translations
This project is translated via [Weblate](https://hosted.weblate.org/engage/ticket-booth/) (preferred). Alternatively, you can translate manually by doing the following:

1. Clone the repository.
2. If it isn't already there, add your language to `/po/LINGUAS`.
3. Create a new translation from the `/po/cartridges.pot` file with a translation editor such as Poedit.
4. Save the file as `[YOUR LANGUAGE CODE].po` to `/po/`.
5. Create a pull request with your translations.

## Building
### Gnome Builder
The quickest and easiest way

1. Install GNOME Builder.
2. Click "Clone Repository" with https://github.com/kra-mo/cartridges.git as the URL.
3. Click on the build button (hammer) at the top.

### Flatpak builder and other IDEs
```shell
git clone https://github.com/aleiepure/ticketbooth
flatpak-builder --repo=/path/to/repo/dir --force-clean --user /path/to/build/dir me.iepure.Ticketbooth.Devel.json
flatpak remote-add --user ticketbooth ticketbooth --no-gpg-verify
flatpak install --user ticketbooth me.iepure.Ticketbooth.Devel
```
Then run with
```shell
flatpak run --user me.iepure.Ticketbooth.Devel
```

## REUSE

This project is REUSE compliant and thus all files must have a license clearly stated at the beginning using this format:

```python
# Copyright (C) <year> <author name>
# SPDX-Licence-Identifier: <SPDX licence (i.e. GPL-3.0-or-later)>
```

using the appropriate comment syntax. If the file is in binary form or doesn't accept comments (i.e. JSON files) use the file `.reuse/dep5` to list files and/or folders with the same information as above using the following syntax

```
Files: <relative path to file>, <relative path to file>, ...
Copyright: <year> <author name>
License: <SPDX licence (i.e. GPL-3.0-or-later)>
```

Files without extensions must be separated into their own section.

Please refer to the [REUSE documentation](https://reuse.readthedocs.io/en/latest/readme.html) to learn how to download and use their tools for compliance checks before opening a pull request.
