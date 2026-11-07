"""Find pixel-identical images and move the newer copies to a duplicates folder."""
import argparse
import hashlib
import os
import shutil
import sys
from pathlib import Path

from PIL import Image

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp'}


def get_image_hash(image_path):
    """Hash of the decoded pixels (plus size and mode). None if unreadable or animated."""
    try:
        with Image.open(image_path) as img:
            if getattr(img, 'n_frames', 1) > 1:
                return None  # multi-frame images: only the first frame would be hashed
            h = hashlib.sha256(f"{img.mode}|{img.size}|".encode())
            h.update(img.tobytes())
            return h.hexdigest()
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None


def handle_duplicate(file_path, duplicate_dir, dry_run=False):
    """Move file_path into duplicate_dir without overwriting anything."""
    duplicate_dir = Path(duplicate_dir)
    file_path = Path(file_path)
    target = duplicate_dir / file_path.name
    counter = 1
    while target.exists():
        target = duplicate_dir / f"{file_path.stem}_({counter}){file_path.suffix}"
        counter += 1
    print(f"Duplicate found: {file_path.name} -> {target}")
    if not dry_run:
        duplicate_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(file_path), str(target))


def find_and_remove_duplicates(directory, duplicate_dir=None, dry_run=False):
    """Move duplicate images under directory into duplicate_dir (default: <directory>/_duplicates)."""
    directory = Path(directory)
    duplicate_dir = Path(duplicate_dir) if duplicate_dir else directory / "_duplicates"
    skip = duplicate_dir.resolve()
    seen = {}
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if (Path(root) / d).resolve() != skip]
        for filename in sorted(files):
            if Path(filename).suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            file_path = Path(root) / filename
            img_hash = get_image_hash(file_path)
            if img_hash is None:
                continue
            if img_hash not in seen:
                seen[img_hash] = file_path
                continue
            original = seen[img_hash]
            # Keep the older file, move the newer one.
            if os.path.getctime(file_path) > os.path.getctime(original):
                handle_duplicate(file_path, duplicate_dir, dry_run)
            else:
                handle_duplicate(original, duplicate_dir, dry_run)
                seen[img_hash] = file_path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', nargs='?', help="directory to scan (default: prompt / current directory)")
    parser.add_argument('-d', '--duplicates-dir', help="where to move duplicates (default: <directory>/_duplicates)")
    parser.add_argument('-n', '--dry-run', action='store_true', help="show what would be moved")
    args = parser.parse_args(argv)

    directory = args.directory or input(
        "Enter directory path (or press Enter for current directory): ").strip() or os.getcwd()
    if not os.path.isdir(directory):
        sys.exit("Invalid directory path!")
    print(f"Scanning directory: {directory}")
    find_and_remove_duplicates(directory, args.duplicates_dir, args.dry_run)
    print("Duplicate check complete!")


if __name__ == "__main__":
    main()
