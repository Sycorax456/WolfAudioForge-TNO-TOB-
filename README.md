# Wolfenstein: The New Order — Audio Tool

A Python/Tkinter tool for extracting and replacing audio in **Wolfenstein: The New Order** (2014, id Tech 5). No external dependencies — pure Python standard library.

## Background

The game stores streamed audio in `.index` files that reference offsets inside separate container files:

| Container            | Slot          |
|-----------------------|---------------|
| `streamed.resources`  | `MAIN_SOUND`  |
| `english.streamed`    | `ENG_SOUND`   |
| `french.streamed`     | `FRA_SOUND`   |
| `italian.streamed`    | `ITA_SOUND`   |
| `spanish.streamed`    | `SPA_SOUND`   |

Each entry in the `.index` describes a filename and, depending on an internal flag, either a single offset/size (main sound effects) or four offsets/sizes — one per localized language track. This tool parses that structure directly in Python (reverse-engineered from a QuickBMS script for the format) instead of shelling out to QuickBMS.

## Features

- **Extract tab** — pick a `.index` + its containers folder, choose which language slots to pull, and export everything as `.ogg`, organized into per-language subfolders.
- **Inject tab** — load a `.index`, browse/filter entries by name and/or language, and replace any entry's audio with your own file:
  - If the replacement is the same size or smaller, it's written **in-place** at the original offset.
  - If it's larger, it's **appended** to the end of the container and the `.index` offset/size fields are patched to point to the new location.
- No repacking of the whole container is needed in either case.

## Requirements

- Python 3.8+
- Tkinter (bundled with most Python installs; on Linux you may need `python3-tk`)

## Usage

```bash
python3 app.py
```

1. **Extract**: select the `.index` file, the folder containing the matching `.streamed`/`.resources` containers, an output folder, tick the languages you want, and hit **Extraer**.
2. **Inject**: select the `.index` and containers folder, click **Cargar entradas** to list everything, filter by name/language, select a row, and click **Reemplazar seleccionada...** to pick your replacement audio file.

## Files

- `app.py` — Tkinter GUI (Extract / Inject tabs)
- `wtno_index_parser.py` — `.index` binary format parser
- `wtno_extractor.py` — extracts raw audio bytes from the containers
- `wtno_injector.py` — patches containers and the `.index` with replacement audio

## Notes / Limitations

- Format details were reverse-engineered from a working QuickBMS script and validated against synthetic test data, not yet against real game files — offsets/sizes should be double-checked against real files before relying on it for a full mod.
- Only `.wav`-suffixed entries are renamed to `.ogg` on export; other extensions are left as-is.
- No game files are included or distributed with this tool.

## Disclaimer

This is a fan-made modding tool. It is not affiliated with or endorsed by MachineGames, Bethesda Softworks, or ZeniMax Media. Use at your own risk and only on files you legally own.
