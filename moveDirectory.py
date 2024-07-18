import shutil
import os
import sys

def copy_directory(src, dst):
    try:
        # Check if the source directory exists
        if not os.path.exists(src):
            print(f"Source directory {src} does not exist.")
            return
        
        # Construct the destination path
        destination = os.path.join(dst, os.path.basename(src))
        
        # Check if the destination directory already exists
        if os.path.exists(destination):
            print(f"Destination directory {destination} already exists.")
            return
        
        # Copy the directory
        shutil.copytree(src, destination)
        print(f"Directory {src} has been copied to {destination}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 copy_directory.py <source_directory> <destination_directory>")
        sys.exit(1)
    
    source_directory = sys.argv[1]
    destination_directory = sys.argv[2]

    copy_directory(source_directory, destination_directory)
