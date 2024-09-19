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
    def __init__(self, source_drive, drive_mirror, engineer_name):

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
        if not os.path.exists(os.path.join(self.DRIVE_MIRROR, self.engineer_name)):
            logger.info("Mirror location does not exist")
            return False
        else:
            logger.info("Mirror location exists")
            return True

    def mirror_change_breakdown(self):
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
        source_file = os.path.join(self.source_drive, new_file[0])
        destination_file = os.path.join(
            self.DRIVE_MIRROR, self.engineer_name, new_file[0]
        )

        os.makedirs(os.path.dirname(destination_file), exist_ok=True)

        shutil.copy2(source_file, destination_file)

        self.mirrored_file = destination_file

    def changed_file_operations(self, changed_file):
        source_file = os.path.join(self.source_drive, changed_file[0])
        destination_file = os.path.join(
            self.DRIVE_MIRROR, self.engineer_name, changed_file[0]
        )
        shutil.copy2(source_file, destination_file)

        self.mirrored_file = destination_file

        if os.path.exists(f"{source_file}.md5"):
            shutil.copy2(f"{source_file}.md5", f"{destination_file}.md5")

    def removed_file_operations(self, removed_file):
        destination_file = os.path.join(
            self.DRIVE_MIRROR, self.engineer_name, removed_file[0]
        )
        os.remove(destination_file)

    def call_checksum_operations(self):
        self.cs.file_checksum_generate(self.mirrored_file)
        self.cs.file_checksum_verify(self.mirrored_file)

        if not self.cs.verified_status:
            os.remove(self.mirrored_file)
            os.remove(f"{self.mirrored_file}.md5")
        else:
            pass

    def commit_file_changes(self):
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
