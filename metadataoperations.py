"""Metadata operations for WAV files.

Provides functionality to extract selected BEXT / container metadata from WAV
files using ffprobe and inject curated values back into the file header using
bwfmetaedit. Intended for use in the backup pipeline to normalise key fields.

External dependencies:
  * ffprobe (part of FFmpeg) must be on PATH
  * bwfmetaedit must be installed and on PATH
"""
import subprocess

from logging_module import logger

class WavHeaderRewrite:
    """Extract and rewrite selected WAV header (BEXT) metadata.

    Workflow:
        1. Call file_bext_export() to parse ffprobe output and cache values.
        2. Call file_info_import() to write normalised fields back into the file.

    Attributes:
        results (dict): Populated after file_bext_export with keys:
            encoded_by, date, creation_time.
    """

    def file_bext_export(self, wav_file):
        """Run ffprobe to capture metadata lines for a WAV file.

        Parses ffprobe stdout and stores mapped fields in self.results.

        Args:
            wav_file (str): Path to the WAV file.
        Raises:
            ValueError: If ffprobe invocation or output reading fails.
        """
        try:
            bext_data = subprocess.Popen(
                ["ffprobe", "-hide_banner", "-i", wav_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except Exception as e:
            logger.critical(f"Error exporting BEXT data for {wav_file}. {e}")
            raise ValueError(e)

        data_map = {
            "encoded_by": "encoded_by",
            "date": "date",
            "creation_time": "creation_time",
        }
        self.results = {
            "encoded_by": "",
            "date": "",
            "creation_time": "",
        }

        try:
            for data in bext_data.stdout.readlines():
                data = data.decode(encoding="utf-8").strip()
        except Exception as e:
            logger.critical(f"Error reading BEXT data for {wav_file}. {e}")
            raise ValueError(e)

        for key, value in data_map.items():
            if key in data:
                self.results[value] = data.split(":")[1].strip()

    def file_info_import(self, wav_file, engineer_name):
        """Inject selected metadata into the WAV file using bwfmetaedit.

        Only proceeds if results dict contains non-empty required fields.

        Args:
            wav_file (str): Path to the WAV file being modified.
            engineer_name (str): Originator/engineer value to embed (ISFT/IENG).
        Raises:
            ValueError: If bwfmetaedit invocation fails.
        """
        if not (
            self.results["encoded_by"] == ""\
            or self.results["date"] == ""\
            or self.results["creation_time"] == ""
        ):
            isft = self.results["encoded_by"]
            icrd = f"{self.results['date']}T{self.results['creation_time'].replace('-', ':')}Z"

            try:
                subprocess.run(
                    [
                        "bwfmetaedit",
                        wav_file,
                        "--append",
                        "--Originator=" + "",
                        "--OriginationDate=" + "",
                        "--OriginationTime=" + "",
                        "--IARL=" + "GB, BL",
                        "--ICRD=" + icrd,
                        "--IENG=" + engineer_name,
                        "--ISFT=" + isft,
                    ],
                    stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL # mute subprocess output
                )
            except Exception as e:
                logger.critical(f"Error importing BEXT data for {wav_file}. {e}")
                raise ValueError(e)
        else:
            pass
