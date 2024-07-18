import os
import shutil
import argparse
from math import ceil
from tqdm import tqdm

def gather_all_files(input_dir):
    """
    Gathers all files from the input directory and its subdirectories.
    """
    all_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            all_files.append(os.path.join(root, file))
    return all_files

def create_output_directories(output_dir, num_splits):
    """
    Creates the output directories for the split files.
    """
    output_dirs = []
    for i in range(num_splits):
        dir_path = os.path.join(output_dir, f'split_{i+1}')
        os.makedirs(dir_path, exist_ok=True)
        output_dirs.append(dir_path)
    return output_dirs

def distribute_files(all_files, output_dirs):
    """
    Distributes files evenly across the output directories.
    """
    num_files = len(all_files)
    num_dirs = len(output_dirs)
    files_per_dir = ceil(num_files / num_dirs)
    
    with tqdm(total=num_files, desc="Distributing files") as pbar:
        for i, file_path in enumerate(all_files):
            dest_dir = output_dirs[i // files_per_dir]
            shutil.move(file_path, dest_dir)
            pbar.update(1)


def split_directory(input_dir, output_dir, num_splits=32):
    """
    Splits the input directory into the specified number of output directories.
    """
    all_files = gather_all_files(input_dir)
    output_dirs = create_output_directories(output_dir, num_splits)
    distribute_files(all_files, output_dirs)

def main():
    parser = argparse.ArgumentParser(description='Split a directory into evenly distributed subdirectories.')
    parser.add_argument('input_dir', type=str, help='Path to the input directory')
    parser.add_argument('output_dir', type=str, help='Path to the output directory')
    parser.add_argument('--num_splits', type=int, default=32, help='Number of splits (default: 32)')

    args = parser.parse_args()

    split_directory(args.input_dir, args.output_dir, args.num_splits)

if __name__ == '__main__':
    main()
