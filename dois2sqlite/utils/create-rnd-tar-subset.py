import logging
import typer
from pathlib import Path
import tarfile
import random
import os
import shutil
DEFAULT_NUM_FILES = 10

def random_files_from_tar(src_path: Path = typer.Argument(..., exists=True), dst_path: Path = typer.Argument(..., exists=False), max_files: int = typer.Option(DEFAULT_NUM_FILES)):
    # Check if the source tar file exists
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Source file {src_path} does not exist.")

    # Create a temporary directory for extracted files
    temp_dir = "temp_extracted_files"
    os.makedirs(temp_dir, exist_ok=True)

    # Open the source tar file
    with tarfile.open(src_path, "r") as src_tar:
        # Get the list of all files in the tar
        logger.info(f"Reading files from {src_path}")
        all_files = [member for member in src_tar.getmembers() if member.isfile()]
        logger.info(f"Found {len(all_files)} files in {src_path}")
        # Select random files
        logger.info(f"Selecting {min(max_files, len(all_files))} random files")
        selected_files = random.sample(all_files, min(max_files, len(all_files)))
        logger.info(f"Selected {len(selected_files)} files")
        # Extract selected files to temporary directory
        for file in selected_files:
            src_tar.extract(file, temp_dir)

    # Create a new tar file with the selected files
    with tarfile.open(dst_path, "w") as dst_tar:
        for file in selected_files:
            file_path = os.path.join(temp_dir, file.name)
            dst_tar.add(file_path, arcname=os.path.basename(file.name))

    # Clean up the temporary directory
    shutil.rmtree(temp_dir)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    typer.run(random_files_from_tar)
# Example usage
# src_path = "/mnt/4tb/all.json.tar"
# dst_path = "/mnt/4tb/10k.json.tar"
# max_files = 2
# random_files_from_tar(src_path, dst_path, max_files)
