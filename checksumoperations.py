"""Checksum operations: generate, write, verify, and clean up MD5 checksum files.

This module provides a small service class used elsewhere in the backup
workflow to create and validate per‑file .md5 sidecar files.
"""

import os
import hashlib
import glob

from logging_module import logger


class ChecksumService:
    """Service for creating and verifying MD5 checksums for files.

    Attributes:
        file_checksum (str|None): Most recently generated checksum hex digest.
        verified_status (bool): Result of last verification attempt.
        failed_files (list[str]): Basenames of files whose checksums failed verification.
    """
    def __init__(self):
        self.file_checksum = None
        self.verified_status = False
        self.failed_files = []

    def file_checksum_generate(self, file):
        """Generate and store the MD5 checksum for the given file path.

        Args:
            file (str): Absolute or relative path to the file whose checksum is required.
        Raises:
            ValueError: If the file cannot be read.
        """
        try:
            file_hash = hashlib.md5()
            with open(file, "rb") as f:
                while chunk := f.read(8192):
                    file_hash.update(chunk)
                self.file_checksum = file_hash.hexdigest()
        except Exception as e:
            logger.critical(f"Error generating checksum for {file}. {e}")
            raise ValueError(e)

    def write_checksum_to_file(self, file, md5_file_name):
        """Write the stored checksum to a .md5 sidecar file in standard format.

        Format written: '<checksum> *<basename>' matching common md5sum output.

        Args:
            file (str): Original file path (used for basename only).
            md5_file_name (str): Target .md5 file path to create/overwrite.
        Raises:
            ValueError: If the checksum file cannot be written.
        """
        try:
            with open(md5_file_name, "w") as md5_file:
                md5_file.write(f"{self.file_checksum} *{os.path.basename(file)}")
        except Exception as e:
            logger.critical(f"Error writing checksum to file {md5_file_name}. {e}")
            raise ValueError(e)

    def file_checksum_verify(self, file):
        """Verify the current stored checksum matches the file's .md5 sidecar.

        Updates verified_status and records failures in failed_files.

        Args:
            file (str): Path to the original file ('.md5' extension is appended).
        Raises:
            ValueError: If the .md5 file cannot be read.
        """
        md5_file_name = f"{file}.md5"
        try:
            with open(md5_file_name, "r") as md5_file:
                md5_string = md5_file.read(32)
        except Exception as e:
            logger.critical(f"Error reading checksum file {md5_file_name}. {e}")
            raise ValueError(e)
        if self.file_checksum == md5_string:
            self.verified_status = True
        else:
            self.verified_status = False
            self.failed_files.append(os.path.basename(file))

    def delete_exisiting_checksums(self, location):  # NOTE: retained original method name (typo) for compatibility
        """Delete all .md5 files in the provided directory.

        Args:
            location (str): Directory path in which to remove '*.md5' files.
        Raises:
            ValueError: If deletion fails for any file.
        """
        try:
            for file in glob.glob(location + "/*.md5"):
                os.remove(file)
        except Exception as e:
            logger.critical(f"Error deleting existing checksum files. {e}")
            raise ValueError(e)
