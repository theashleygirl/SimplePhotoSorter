import os
from PIL import Image
import hashlib
from datetime import datetime
import shutil

def get_image_hash(image_path):
    """Calculate image hash using its content"""
    try:
        with Image.open(image_path) as img:
            # Convert image to bytes
            img_byte_arr = img.tobytes()
            # Create hash object
            hash_obj = hashlib.md5(img_byte_arr)
            return hash_obj.hexdigest()
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None

def handle_duplicate(file_path):
    duplicate_dir = r"C:\Users\neonr\Desktop\File Tree\Images & Videos\Images\IRL\EnthusiastPhotog\Duplicates"
    
    # Create duplicates directory if it doesn't exist
    if not os.path.exists(duplicate_dir):
        os.makedirs(duplicate_dir)
    
    # Get filename from path
    file_name = os.path.basename(file_path)
    
    # Create path for duplicate file
    duplicate_path = os.path.join(duplicate_dir, file_name)
    
    # Log the duplicate
    print(f"Duplicate found: {file_name}")
    
    # Move file to duplicates folder
    shutil.move(file_path, duplicate_path)

def find_and_remove_duplicates(directory):
    """Find and remove duplicate images in the specified directory"""
    # Dictionary to store image hashes and their paths
    image_hashes = {}
    
    # Supported image formats
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    
    # Walk through the directory
    for root, _, files in os.walk(directory):
        for filename in files:
            if any(filename.lower().endswith(ext) for ext in image_extensions):
                file_path = os.path.join(root, filename)
                
                # Get image hash
                img_hash = get_image_hash(file_path)
                if img_hash is None:
                    continue
                
                # If we've seen this hash before
                if img_hash in image_hashes:
                    # Get creation times for both files
                    original_time = os.path.getctime(image_hashes[img_hash])
                    duplicate_time = os.path.getctime(file_path)
                    
                    # Move the newer file to duplicates folder
                    if duplicate_time > original_time:
                        handle_duplicate(file_path)
                    else:
                        handle_duplicate(image_hashes[img_hash])
                        image_hashes[img_hash] = file_path
                else:
                    # First time seeing this hash
                    image_hashes[img_hash] = file_path

if __name__ == "__main__":
    # Get the directory path from user input or use current directory
    directory = input("Enter directory path (or press Enter for current directory): ").strip()
    if not directory:
        directory = os.getcwd()
    
    if os.path.exists(directory):
        print(f"Scanning directory: {directory}")
        find_and_remove_duplicates(directory)
        print("Duplicate removal complete!")
    else:
        print("Invalid directory path!")
