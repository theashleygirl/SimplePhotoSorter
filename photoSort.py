"""Rename and/or sort photos and videos into Year / Month / ISO-week folders."""
import argparse
import calendar
import datetime
import os
import shutil
import sys
from pathlib import Path

from PIL import Image

EXIF_IFD_POINTER = 0x8769
TAG_DATETIME_ORIGINAL = 0x9003

EXIF_EXTENSIONS = {'.jpg', '.jpeg', '.tif', '.tiff', '.png', '.webp'}
MEDIA_EXTENSIONS = EXIF_EXTENSIONS | {
    '.gif', '.bmp', '.raw', '.cr2', '.nef',
    '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp',
}
EXIF_DATE_FORMAT = '%Y:%m:%d %H:%M:%S'


def get_date_time_original(filepath):
    """Return the EXIF DateTimeOriginal string of an image, or None."""
    try:
        with Image.open(filepath) as image:
            exif = image.getexif()
            value = exif.get_ifd(EXIF_IFD_POINTER).get(TAG_DATETIME_ORIGINAL)
            if isinstance(value, bytes):
                value = value.decode('ascii', errors='ignore')
            return value.strip('\x00 ') if value else None
    except Exception as e:
        print(f"Error extracting DateTimeOriginal from {filepath}: {e}")
        return None


def is_media(path):
    return Path(path).suffix.lower() in MEDIA_EXTENSIONS


def iter_media(source_dir, exclude_dir=None):
    """Return a list of media files under source_dir, skipping exclude_dir."""
    exclude = Path(exclude_dir).resolve() if exclude_dir else None
    found = []
    for root, dirs, files in os.walk(source_dir):
        if exclude:
            dirs[:] = [d for d in dirs if (Path(root) / d).resolve() != exclude]
        found.extend(Path(root) / f for f in files if is_media(f))
    return found


def get_media_date(file_path):
    """Date from EXIF where available, otherwise the modification time."""
    if file_path.suffix.lower() in EXIF_EXTENSIONS:
        date_str = get_date_time_original(file_path)
        if date_str:
            try:
                return datetime.datetime.strptime(date_str, EXIF_DATE_FORMAT)
            except ValueError:
                print(f"Invalid date format in {file_path.name}")
    return datetime.datetime.fromtimestamp(os.path.getmtime(file_path))


def get_week_dates(iso_year, week_num):
    """Start and end (dd.mm) of an ISO week; iso_year is the ISO year."""
    first_day = datetime.datetime.strptime(f'{iso_year}-W{week_num:02d}-1', '%G-W%V-%u')
    last_day = first_day + datetime.timedelta(days=6)
    return first_day.strftime('%d.%m'), last_day.strftime('%d.%m')


def unique_path(path):
    """Return path, or path with a numeric suffix if it already exists."""
    candidate, counter = path, 1
    while candidate.exists():
        candidate = path.with_name(f"{path.stem}_({counter}){path.suffix}")
        counter += 1
    return candidate


def rename_file(file_path, date_time, dry_run=False):
    """Rename a file based on its date and time. Never overwrites."""
    try:
        date_time_obj = datetime.datetime.strptime(date_time, EXIF_DATE_FORMAT)
        base = date_time_obj.strftime('%Y_%m_%d_%H%M%S')
        target = file_path.with_name(f"{base}{file_path.suffix}")
        if target == file_path:
            return file_path
        target = unique_path(target)
        if not dry_run:
            file_path.rename(target)
        print(f"Renamed '{file_path.name}' to '{target.name}'")
        return target
    except Exception as e:
        print(f"Error renaming file {file_path}: {e}")
        return file_path


def sort_file(current_path, media_date, output_dir, dry_run=False):
    """Move a file into output_dir/Year/MM - Month/Www - start - end."""
    iso_year, week_num, _ = media_date.isocalendar()
    week_start, week_end = get_week_dates(iso_year, week_num)
    month_name = calendar.month_name[media_date.month]
    dest_dir = (Path(output_dir) / str(media_date.year)
                / f"{media_date.month:02d} - {month_name}"
                / f"W{week_num:02d} - {week_start} - {week_end}")
    new_filepath = unique_path(dest_dir / current_path.name)
    try:
        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(current_path), str(new_filepath))
        print(f"Moved '{current_path.name}' to '{new_filepath}'")
    except Exception as e:
        print(f"Error moving {current_path}: {e}")


def process_media(source_dir, output_dir=None, should_rename=False,
                  should_sort=False, assume_yes=False, dry_run=False):
    """Process media files with options to rename and/or sort."""
    if should_sort and not output_dir:
        print("Error: Output directory required for sorting.")
        return
    if not Path(source_dir).is_dir():
        print(f"Error: '{source_dir}' is not a directory.")
        return

    files = iter_media(source_dir, output_dir if should_sort else None)
    print(f"\nFound {len(files)} media files in the source directory.")
    if not assume_yes:
        confirmation = input(f"Do you want to proceed with processing {len(files)} files? (y/n): ")
        if confirmation.strip().lower() != 'y':
            print("Operation cancelled by user.")
            return

    for file_path in files:
        media_date = get_media_date(file_path)
        current_path = file_path
        if should_rename:
            current_path = rename_file(file_path, media_date.strftime(EXIF_DATE_FORMAT), dry_run)
        if should_sort:
            sort_file(current_path, media_date, output_dir, dry_run)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?', help="source directory")
    parser.add_argument('-o', '--output', help="output directory (sorting)")
    parser.add_argument('--mode', choices=['rename', 'sort', 'both'], help="what to do")
    parser.add_argument('-n', '--dry-run', action='store_true', help="show what would happen")
    parser.add_argument('-y', '--yes', action='store_true', help="skip confirmation prompt")
    args = parser.parse_args(argv)

    source_dir = args.source or input("Enter the source directory path: ").strip()
    if not source_dir:
        sys.exit("Error: Source directory path is empty.")

    mode = args.mode
    if not mode:
        print("\nWhat would you like to do?")
        print("1. Rename files only")
        print("2. Sort files only")
        print("3. Rename and sort files")
        mode = {'1': 'rename', '2': 'sort', '3': 'both'}.get(input("Enter your choice (1-3): ").strip())
        if not mode:
            sys.exit("Error: invalid choice.")

    should_rename = mode in {'rename', 'both'}
    should_sort = mode in {'sort', 'both'}
    output_dir = args.output
    if should_sort and not output_dir:
        output_dir = input("Enter the output directory path: ").strip()
        if not output_dir:
            sys.exit("Error: Output directory path is empty.")

    process_media(source_dir, output_dir, should_rename, should_sort, args.yes, args.dry_run)


if __name__ == "__main__":
    main()
