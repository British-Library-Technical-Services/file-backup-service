"""Post backup operations for generated access files.

This module handles:
  * Deriving collection (shelfmark) identifiers from WAV filenames.
  * Generating compressed AAC (.m4a) access copies using ffmpeg.
  * Moving / updating access copies into the MSO store organised by collection.

External tools assumed on PATH: ffmpeg.
Environment variables used: MSO_STORE (destination root for access copies).
"""
import os
import subprocess
import shutil
from dotenv import load_dotenv

from logging_module import logger

load_dotenv()


class PostBackupOperations:
    """Operations executed after primary file backup.

    Args:
        staging_location (str): Path where intermediate / generated files are written.

    Attributes:
        MSO_STORE (str): Root directory for access (m4a) files, from env.
        collection_no (str|None): Parsed collection identifier from current WAV.
        STAGING_LOCATION (str): Provided staging path.
        m4a_file (str|None): Placeholder for last generated access file path.
    """
    def __init__(self, staging_location):
        self.MSO_STORE = os.getenv("MSO_STORE")
        self.collection_no = None
        self.STAGING_LOCATION = staging_location
        self.m4a_file = None

    def get_shelfmark(self, wav_file):
        """Parse WAV filename to set collection_no attribute.

        Expected filename pattern segments separated by underscores. Logic:
          * If second token starts with 1/2/9 -> first three characters.
          * If it starts with 'C' -> token up to first '-'.
          * Else: entire second token.

        Args:
            wav_file (str): Path to the WAV file.
        Raises:
            ValueError: On parsing errors.
        """
        try:
            self.wav_file_name = os.path.basename(wav_file.split(".")[0])
            parsed_name = self.wav_file_name.split("_")
            if parsed_name[1].startswith(("1", "2", "9")):
                self.collection_no = parsed_name[1][0:3]
            elif parsed_name[1].startswith("C"):
                self.collection_no = parsed_name[1].split("-")[0]
            else:
                self.collection_no = parsed_name[1]
        except Exception as e:
            logger.warning(f"Error parsing shelfmark for {wav_file}. {e}")
            raise ValueError(e)

    def move_to_mso_store(self, m4a_file):
        """Move (or replace) an access .m4a file into its collection directory.

        Creates the collection directory if needed. If a file with the same name
        already exists it is replaced.

        Args:
            m4a_file (str): Path to the generated access file.
        Raises:
            ValueError: If move or removal operations fail.
        """
        collection_directory = os.path.join(self.MSO_STORE, self.collection_no)
        try:
            if not os.path.exists(collection_directory):
                os.mkdir(collection_directory)
                shutil.move(m4a_file, collection_directory)
            elif os.path.exists(os.path.join(collection_directory, os.path.basename(m4a_file))):
                os.remove(os.path.join(collection_directory, os.path.basename(m4a_file)))
                shutil.move(m4a_file, collection_directory)
            else:
                shutil.move(m4a_file, collection_directory)
        except Exception as e:
            logger.critical(f"Error moving {m4a_file} to MSO store. {e}")
            raise ValueError(e)

    def access_file_generate(self, wav_file):
        """Generate an AAC (.m4a) access copy for a WAV file and move it to MSO.

        Uses ffmpeg with fixed parameters (AAC 256k, audio only). On success the
        file is moved into the MSO_STORE collection directory derived via
        get_shelfmark().

        Args:
            wav_file (str): Path to source WAV.
        Raises:
            ValueError: If ffmpeg invocation fails.
        """
        wav_file_name = os.path.basename(wav_file.split(".")[0])
        m4a_file = os.path.join(self.STAGING_LOCATION, f"{wav_file_name}.m4a")
        try:
            subprocess.call(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "panic",
                    "-y",
                    "-i",
                    wav_file,
                    "-c:a",
                    "aac",
                    "-b:a",
                    "256k",
                    "-vn",
                    m4a_file,
                ],
            )
        except Exception as e:
            logger.critical(f"Error generating access file for {wav_file}. {e}")
            raise ValueError(e)
        self.move_to_mso_store(m4a_file)
