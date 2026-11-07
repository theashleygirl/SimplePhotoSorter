# SimplePhotoSorter

After spending so much time taking photos over the last few months, I decided to make a basic photo sorter to help tidy up my mess.

Two small Python scripts built on [Pillow](https://python-pillow.github.io/).

## Install

Requires Python 3.10+ (Pillow 13).

```sh
pip install -r requirements.txt
```

## photoSort.py

Renames media to `YYYY_MM_DD_HHMMSS.ext` (from EXIF `DateTimeOriginal`, falling back to the file's modified time) and/or moves it into `Year/MM - Month/Www - dd.mm - dd.mm/` (ISO weeks).

```sh
python photoSort.py                       # interactive prompts
python photoSort.py ~/Photos --mode both -o ~/Sorted --dry-run
```

Options: `--mode rename|sort|both`, `-o/--output`, `-n/--dry-run` (change nothing), `-y/--yes` (skip confirmation). Existing files are never overwritten; name clashes get a `_(n)` suffix. Files are **moved**, so try `--dry-run` first and keep a backup.

## duplicateChecker.py

Finds images (jpg, png, bmp) with identical pixels and moves the newer copy to a duplicates folder (default `<directory>/_duplicates`). Animated/multi-frame images are skipped.

```sh
python duplicateChecker.py ~/Photos --dry-run
python duplicateChecker.py ~/Photos -d ~/Duplicates
```

## Tests

```sh
pip install -r requirements-dev.txt
pytest
```

## License

MIT, see [LICENSE](LICENSE).
