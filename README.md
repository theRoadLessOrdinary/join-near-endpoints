# Join Near Endpoints

An Inkscape extension that joins the loose ends inside a path when they sit close together, so broken pieces become one continuous line.

Menu: **Extensions > Map's Edge Tools > General > Paths > Join Near Endpoints** (extension ID `maps_edge.join_near_endpoints`).

## Using it

1. Select one or more paths.
2. Run **Join Near Endpoints** and set **Join endpoints closer than (mm)** (default 0.3).

Inside each selected path:

- Every pair of open subpath ends closer than that distance is joined into one node.
- The joined node goes halfway between the two old ends. The handles on each side move with it, so curve shapes are kept.
- Each end is joined at most once, nearest pairs first.
- A piece whose ends lead back around to its own start becomes a closed subpath.
- Pieces are reversed where needed so the joined subpath runs one way.
- Closed subpaths, and ends with no partner in range, are left as they are.

Only subpaths inside the same path are joined; to join separate paths, combine them first (**Path > Combine**). The distance is measured on the canvas in millimeters, after any transforms on the path and its groups.

## Requirements

- Inkscape 1.x (developed and used on Inkscape 1.4.4, Flatpak, on Linux; other platforms have not been tried)

## Install

Copy the files in this repository into a folder of their own inside Inkscape's user extensions directory, then restart Inkscape. To find that directory, open **Edit > Preferences > System** and look at **User extensions**. Typical locations:

| Install type | User extensions folder |
|---|---|
| Linux (native) | `~/.config/inkscape/extensions/` |
| Linux (Flatpak) | `~/.var/app/org.inkscape.Inkscape/config/inkscape/extensions/` |
| macOS | `~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/` |
| Windows | `%APPDATA%\inkscape\extensions\` |

For example, on native Linux:

```bash
git clone https://github.com/theRoadLessOrdinary/join-near-endpoints.git \
    ~/.config/inkscape/extensions/join-near-endpoints
```

To uninstall, delete the folder and restart Inkscape.
