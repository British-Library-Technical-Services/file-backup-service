"""Drive mirroring operations.

Determines differences between a source engineer drive and its mirror, then
applies incremental updates (new / changed / removed files) while optionally
validating associated checksum sidecar files (.md5) when present.
"""

import os
import glob
import shutil
from dotenv import load_dotenv
from rich import print
from rich.prompt import Prompt
import sys
import time

from logging_module import logger
from checksumoperations import ChecksumService
from progressbar import progress_bar
from messageoperations import MessagingService


load_dotenv()


class DriveMirror:
    """Incrementally mirror a source drive into a destination engineer folder.

    Attributes:
        source_drive (str): Root path of the engineer's source drive.
        DRIVE_MIRROR (str): Root path where engineer mirrors are stored.
        engineer_name (str): Engineer folder name under DRIVE_MIRROR.
        mirrored_file (str|None): Path of the most recently copied file.
        source_file_paths (list[tuple[str,int]]): Relative paths + sizes in source.
        mirror_file_paths (list[tuple[str,int]]): Relative paths + sizes in mirror.
        new_files_in_source (list[tuple[str,int]]): Files present only in source.
        changed_files_in_source (list[tuple[str,int]]): Same path but different size.
        removed_files_in_source (list[tuple[str,int]]): Files no longer in source.
        cs (ChecksumService): Checksum service instance for validation.
        ms (MessagingService): Messaging/UX helper for prompts.
        progress_bar (callable): Progress bar function for CLI feedback.
    """

    def __init__(self, source_drive, drive_mirror, engineer_name):
        """Initialize a new DriveMirror instance.

        Args:
            source_drive (str): Source drive root path.
            drive_mirror (str): Destination root path for mirrors.
            engineer_name (str): Engineer identifier / folder name.
        """
        self.source_drive = source_drive
        self.DRIVE_MIRROR = drive_mirror
        self.engineer_name = engineer_name
        self.mirrored_file = None
        self.source_file_paths = []
        self.mirror_file_paths = []
        self.new_files_in_source = []
        self.changed_files_in_source = []
        self.removed_files_in_source = []
        self.cs = ChecksumService()
        self.ms = MessagingService()
        self.progress_bar = progress_bar

    def check_mirror_location(self):
        """Return True if engineer mirror folder exists, else False."""
        if not os.path.exists(os.path.join(self.DRIVE_MIRROR, self.engineer_name)):
            logger.info("Mirror location does not exist")
            return False
        else:
            logger.info("Mirror location exists")
            return True

    def mirror_change_breakdown(self):
        """Print a summary of new, changed, and removed files pending commit."""
        print(f"\n[bold]New Files: {len(self.new_files_in_source)}[/bold]")
        for new_file in self.new_files_in_source:
            print(f" * {new_file[0]}")

        print(f"\n[bold]Changed Files: {len(self.changed_files_in_source)}[/bold]")
        for changed_file in self.changed_files_in_source:
            print(f" * {changed_file[0]}")

        print(f"\n[bold]Removed Files: {len(self.removed_files_in_source)}[/bold]")
        for removed_file in self.removed_files_in_source:
            print(f" * {removed_file[0]}")

    def check_source_mirror_changes(self):
        """Populate diff lists (new/changed/removed) between source and mirror.

        Returns:
            bool: True if any differences are detected, False otherwise.
        """
        full_source_list = glob.glob(
            os.path.join(self.source_drive, "**/*.*"),
            recursive=True,
        )

        full_destination_list = glob.glob(
            os.path.join(self.DRIVE_MIRROR, self.engineer_name, "**/*.*"),
            recursive=True,
        )

        for source_file in full_source_list:
            source_file_size = os.path.getsize(source_file)
            relative_source_path = os.path.relpath(
                source_file, os.path.join(self.source_drive)
            )
            self.source_file_paths.append((relative_source_path, source_file_size))

        for destination_file in full_destination_list:
            mirror_file_size = os.path.getsize(destination_file)
            relative_mirror_path = os.path.relpath(
                destination_file, os.path.join(self.DRIVE_MIRROR, self.engineer_name)
            )
            self.mirror_file_paths.append((relative_mirror_path, mirror_file_size))

        self.new_files_in_source = [
            key
            for key in self.source_file_paths
            if key[0] not in [source_key[0] for source_key in self.mirror_file_paths]
        ]

        self.changed_files_in_source = [
            source_key
            for source_key in self.source_file_paths
            for mirror_key in self.mirror_file_paths
            if source_key[0] == mirror_key[0] and source_key[1] != mirror_key[1]
        ]

        self.removed_files_in_source = [
            key
            for key in self.mirror_file_paths
            if key[0] not in [mirror_key[0] for mirror_key in self.source_file_paths]
        ]

        logger.info(
            f"{len(self.new_files_in_source)} new files, {len(self.changed_files_in_source)} changed files, {len(self.removed_files_in_source)} removed files"
        )

        if (
            self.new_files_in_source != []
            or self.changed_files_in_source != []
            or self.removed_files_in_source != []
        ):
            return True
        else:
            return False

    def new_file_operations(self, new_file):
        """Mirror a new file (create directories, copy, track last copied)."""
        source_file = os.path.join(self.source_drive, new_file[0])
        destination_file = os.path.join(
            self.DRIVE_MIRROR, self.engineer_name, new_file[0]
        )

        os.makedirs(os.path.dirname(destination_file), exist_ok=True)

        shutil.copy2(source_file, destination_file)

        self.mirrored_file = destination_file

    def changed_file_operations(self, changed_file):
        """Copy an updated file overwriting mirror copy and preserve checksum if present."""
        source_file = os.path.join(self.source_drive, changed_file[0])
        destination_file = os.path.join(
            self.DRIVE_MIRROR, self.engineer_name, changed_file[0]
        )
        shutil.copy2(source_file, destination_file)

        self.mirrored_file = destination_file

        if os.path.exists(f"{source_file}.md5"):
            shutil.copy2(f"{source_file}.md5", f"{destination_file}.md5")

    def removed_file_operations(self, removed_file):
        """Remove a file from the mirror that no longer exists in the source."""
        destination_file = os.path.join(
            self.DRIVE_MIRROR, self.engineer_name, removed_file[0]
        )
        os.remove(destination_file)

    def call_checksum_operations(self):
        """Generate + verify checksum for the last mirrored file; delete if invalid."""
        self.cs.file_checksum_generate(self.mirrored_file)
        self.cs.file_checksum_verify(self.mirrored_file)

        if not self.cs.verified_status:
            os.remove(self.mirrored_file)
            os.remove(f"{self.mirrored_file}.md5")
        else:
            pass

    def commit_file_changes(self):
        """Apply pending new/changed/removed file operations with progress + validation."""
        if self.new_files_in_source != []:
            print("\n[bold magenta]Mirroring new files...[/bold magenta]")
            for index, new_file in enumerate(self.new_files_in_source):
                self.progress_bar(index, len(self.new_files_in_source))
                self.new_file_operations(new_file)

                logger.info(f"New file {new_file[0]} mirrored")

                if os.path.exists(f"{self.mirrored_file}.md5"):
                    self.call_checksum_operations()
                else:
                    pass

        if self.changed_files_in_source != []:
            print("\n[bold magenta]Updating changed files...[/bold magenta]")
            for index, changed_file in enumerate(self.changed_files_in_source):
                self.progress_bar(index, len(self.changed_files_in_source))
                self.changed_file_operations(changed_file)

                logger.info(f"Changed file {changed_file[0]} mirrored")

                if os.path.exists(f"{self.mirrored_file}.md5"):
                    self.call_checksum_operations()
                else:
                    pass

        if self.removed_files_in_source != []:
            print("\n[bold magenta]Removing deleted files...[/bold magenta]")
            for index, removed_file in enumerate(self.removed_files_in_source):
                self.progress_bar(index, len(self.removed_files_in_source))
                self.removed_file_operations(removed_file)

                logger.info(f"Removed file {removed_file[0]}")

        if self.cs.failed_files != []:

            logger.critical(f"Checksum verification failed for {self.cs.failed_files}")

            print(
                "\n[bold red]New and/or updated files with checksums have failed validation[/bold red] and will be removed from the backup location!"
            )
            for failed_file in self.cs.failed_files:
                print(f" * {failed_file}")

            print(f"\nPlease check the files and try again.")
        else:
            logger.info("All with exisiting checksum files validated")
            print(
                "\n[bold green]New and/or updated files with checksums have all validated![/bold green]"
            )

    def run_drive_mirror_operations(self):
        """Main orchestration method to detect, review, and apply mirror changes."""
        logger.info("Drive mirror operations initiated")

        if self.check_mirror_location():
            if self.check_source_mirror_changes():
                print(self.ms.drive_mirror_message(self.engineer_name))
                response = Prompt.ask(self.ms.view_or_run)

                if response == "v":
                    self.mirror_change_breakdown()
                    commit_changes = Prompt.ask(
                        "\nPress [bold magenta]any key[/bold magenta] to commit changes or [bold yellow]'q'[/bold yellow] to quit"
                    )
                    if not commit_changes == "q":
                        self.commit_file_changes()
                    else:
                        logger.info("User cancelled the operation")
                        print("Sayonara!")
                        time.sleep(2)
                        sys.exit()

                else:
                    self.commit_file_changes()

            else:
                logger.info("User cancelled the operation")
                print(
                    "[bold yellow]No changes have been detected[/bold yellow], service will exit."
                )
                time.sleep(2)
                sys.exit()

        else:
            self.check_source_mirror_changes()
            print(self.ms.drive_mirror_message(self.engineer_name))
            response = Prompt.ask(self.ms.view_or_run)

            if response == "v":
                self.mirror_change_breakdown()
                commit_changes = Prompt.ask(
                    "\nPress [bold magenta]any key[/bold magenta] to commit changes or [bold yellow]'q'[/bold yellow] to quit"
                )
                if not commit_changes == "q":
                    self.commit_file_changes()

                else:
                    logger.info("User cancelled the operation")
                    print("Sayonara!")
                    time.sleep(2)
                    sys.exit()
