import os
import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import shutil
from pathlib import Path
import calendar

def get_date_time_original(filepath):
    """Extracts the date and time from image/video metadata."""
    try:
        image = Image.open(filepath)
        info = image._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "DateTimeOriginal":
                    return value
        return None
    except Exception as e:
        print(f"Error extracting DateTimeOriginal: {e}")
        return None

def count_files(directory):
    """Counts total number of files in directory and subdirectories."""
    total_files = 0
    for root, dirs, files in os.walk(directory):
        total_files += len(files)
    return total_files

def get_week_dates(year, week_num):
    """Get start and end dates for a given week number."""
    # Use ISO week format directly without subtraction
    first_day = datetime.datetime.strptime(f'{year}-W{week_num:02d}-1', '%G-W%V-%u')
    last_day = first_day + datetime.timedelta(days=6)
    return first_day.strftime('%d.%m'), last_day.strftime('%d.%m')

def rename_file(file_path, date_time):
    """Rename a file based on its date and time."""
    try:
        date_time_obj = datetime.datetime.strptime(date_time, '%Y:%m:%d %H:%M:%S')
        new_filename_base = date_time_obj.strftime('%Y_%m_%d_%H%M%S')
        suffix = file_path.suffix
        counter = 1
        new_filename = f"{new_filename_base}{suffix}"
        new_filepath = file_path.parent / new_filename
        
        while new_filepath.exists():
            new_filename = f"{new_filename_base}_({counter}){suffix}"
            new_filepath = file_path.parent / new_filename
            counter += 1
            
        file_path.rename(new_filepath)
        return new_filepath
    except Exception as e:
        print(f"Error renaming file {file_path}: {e}")
        return file_path

def process_media(source_dir, output_dir=None, should_rename=False, should_sort=False):
    """Process media files with options to rename and/or sort."""
    if should_sort and not output_dir:
        print("Error: Output directory required for sorting.")
        return
        
    if should_sort:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    media_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.raw', '.cr2', '.nef',
        '.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v', '.3gp'
    }
    
    total_files = count_files(source_dir)
    print(f"\nFound {total_files} files in the source directory.")
    confirmation = input(f"Do you want to proceed with processing {total_files} files? (y/n): ")
    
    if confirmation.lower() != 'y':
        print("Operation cancelled by user.")
        return

    for root, _, files in os.walk(source_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in media_extensions):
                file_path = Path(root) / file
                
                date_str = get_date_time_original(file_path) if file_path.suffix.lower() in {'.jpg', '.jpeg', '.tiff'} else None
                if date_str:
                    try:
                        media_date = datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                    except ValueError:
                        print(f"Invalid date format in {file}")
                        media_date = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                else:
                    media_date = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

                current_path = file_path
                
                if should_rename:
                    new_path = rename_file(file_path, media_date.strftime('%Y:%m:%d %H:%M:%S'))
                    current_path = new_path
                    print(f"Renamed '{file}' to '{new_path.name}'")

                if should_sort:
                    week_num = media_date.isocalendar()[1]
                    week_start, week_end = get_week_dates(media_date.year, week_num)
                    month_name = calendar.month_name[media_date.month]
                    
                    dest_path = Path(output_dir) / str(media_date.year) / \
                              f"{media_date.month:02d} - {month_name}" / \
                              f"W{week_num:02d} - {week_start} - {week_end}"
                    
                    dest_path.mkdir(parents=True, exist_ok=True)
                    new_filepath = dest_path / current_path.name
                    
                    counter = 1
                    while new_filepath.exists():
                        new_filepath = dest_path / f"{current_path.stem}_{counter}{current_path.suffix}"
                        counter += 1
                    
                    shutil.move(current_path, new_filepath)
                    print(f"Moved '{current_path.name}' to '{new_filepath}'")

if __name__ == "__main__":
    source_dir = input("Enter the source directory path: ")
    if not source_dir:
        print("Error: Source directory path is empty.")
        exit()
    
    print("\nWhat would you like to do?")
    print("1. Rename files only")
    print("2. Sort files only")
    print("3. Rename and sort files")
    choice = input("Enter your choice (1-3): ")
    
    should_rename = choice in {'1', '3'}
    should_sort = choice in {'2', '3'}
    
    output_dir = None
    if should_sort:
        output_dir = input("Enter the output directory path: ")
        if not output_dir:
            print("Error: Output directory path is empty.")
            exit()
    
    process_media(source_dir, output_dir, should_rename, should_sort)
