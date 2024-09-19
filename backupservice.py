import logging
import os
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
import glob
import shutil

from dotenv import load_dotenv
from rich import print
from rich.prompt import Prompt


from messageoperations import MessagingService
import userlist
from checksumoperations import ChecksumService
from metadataoperations import WavHeaderRewrite
from postoperations import PostBackupOperations
from drivemirroroperations import DriveMirror
from progressbar import progress_bar, cycling_progress
from logging_module import logger

load_dotenv()

root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)


class BackupFileService:
    def __init__(self):

        self.STAGING_LOCATION = os.getenv("STAGING_LOCATION")
        self.ROOT_BACKUP = os.getenv("ROOT_BACKUP")
        self.BAU_ENGINEER_1 = os.getenv("BAU_ENGINEER_1")
        self.BAU_ENGINEER_2 = os.getenv("BAU_ENGINEER_2")

        self.source_directory = None
        self.collection_no = None
        self.engineer_name = None

        self.staging_file_list = None
        self.batch_copy = None
        self.mirror_in_progress = False

        self.cs = ChecksumService()
        self.whr = WavHeaderRewrite()
        self.ms = MessagingService()
        self.pbo = PostBackupOperations(self.STAGING_LOCATION)
        self.progress_bar = progress_bar

    def clear_staging_area(self):
        staging_file_check = glob.glob(self.STAGING_LOCATION + "/*.*")
        if staging_file_check != []:
            logger.warning(f"Files found in staging area")
            for file in staging_file_check:
                os.remove(file)
                logger.warning(f"{file} removed from staging area")
        else:
            logger.info(f"staging area clear")

    def set_source_and_engineer(self):

        Prompt.ask(self.ms.welcome_messgage)

        source_drive_select = filedialog.askdirectory(initialdir="/media/quadriga/")
        if source_drive_select == "":
            logger.warning(f"User cancelled source directory selection. Exiting.")
            raise ValueError(self.ms.user_cancel)
        else:
            source_dir_list = [
                dir
                for dir in os.listdir(source_drive_select)
                if os.path.isdir(os.path.join(source_drive_select, dir))
            ]
            if source_dir_list != []:
                for source_dir in source_dir_list:
                    if source_dir.casefold() in map(str.casefold, userlist.engineers):
                        self.engineer_name = next(
                            engineer
                            for engineer in userlist.engineers
                            if engineer.casefold() == source_dir.casefold()
                        )
                        self.source_directory = os.path.join(
                            source_drive_select, source_dir
                        )
                        logger.info(f"{self.engineer_name} started service")
                        logger.info(f"Source directory set to {self.source_directory}")
                        break
            else:
                logger.warning(f"No directories found. Exiting.")
                raise ValueError(self.ms.empty_directory)

            if self.engineer_name is None:
                logger.warning(f"No directory matches engineer name in list. Exiting.")
                raise ValueError(self.ms.no_engineer_match)
            else:
                return self.engineer_name

    def copy_files_to_staging(self):
        logger.info(f"copy_files_to_staging started for {self.engineer_name}")

        file_list = glob.glob(self.source_directory + "/*.*")

        if file_list == []:
            logger.critical(f"No files found in source directory. Exiting.")
            raise ValueError(self.ms.no_files_found)

        if not any("_ExcelBatchUpload.xlsx" in file for file in file_list):
            logger.critical(f"Batch SIP spreadsheet missing. Exiting.")
            raise ValueError(self.ms.batch_sip_spreadsheet_missing)
        
        else:
            # exclude_md5_file_list = [f for f in file_list if not f.endswith(".md5")]

            for file in file_list:
                logger.info(f"{file} will be copied to staging area")

            while True:  # start backup service and view criteria option
                response = Prompt.ask(
                    self.ms.engineer_file_data(self.engineer_name, file_list)
                )
                if response == "v":
                    Prompt.ask(self.ms.collection_backup_message)
                else:
                    break

            print(self.ms.copy_files_to_staging)

            for index, file in enumerate(file_list):
                self.progress_bar(index, len(file_list))
                staging_file_copy = os.path.join(
                    self.STAGING_LOCATION, os.path.basename(file)
                )
                if file.endswith(".md5"):
                    pass
                elif file.endswith(".wav"):
                    md5_file_name = f"{file}.md5"

                    if os.path.exists(md5_file_name):
                        self.cs.file_checksum_generate(file)
                    else:
                        self.cs.file_checksum_generate(file)
                        self.cs.write_checksum_to_file(file, md5_file_name)
                        logger.info(f"Generated checksum for {file}")

                    shutil.copy2(file, staging_file_copy)
                    logger.info(f"{file} copied to staging area")

                    shutil.copy2(md5_file_name, f"{staging_file_copy}.md5")
                    logger.info(f"{md5_file_name} copied to staging area")

                    self.cs.file_checksum_verify(staging_file_copy)
                    logger.info(f"Checksum verification check for {staging_file_copy}")
                else:
                    shutil.copy2(file, staging_file_copy)
                    logger.info(f"{file} copied to staging area")

            if self.cs.failed_files != []:
                logger.critical(
                    f"Checksum verification failed for {self.cs.failed_files}"
                )
                raise ValueError(
                    f"""
{self.ms.checksum_fail}
Failed Files: {len(self.cs.failed_files)}; {self.cs.failed_files}"""
                )
            else:
                print(self.ms.checksum_pass)
                logger.info(f"Checksum verification passed for all files")

    def drive_eject_request(self):
        print(self.ms.eject_drive)

        logger.info(f"{self.source_directory} ejected drive")

    def post_copy_operations(self):
        logger.info(f"post_copy_operations started for {self.engineer_name}")

        print(self.ms.post_copy_operations)

        self.cs.delete_exisiting_checksums(self.STAGING_LOCATION)
        logger.info(f"Deleted existing checksums in {self.STAGING_LOCATION}")

        self.staging_file_list = glob.glob(self.STAGING_LOCATION + "/*.*")

        for index, file in enumerate(self.staging_file_list):
            self.progress_bar(index, len(self.staging_file_list))
            if file.endswith(".wav"):
                wav_file = file
                self.whr.file_bext_export(wav_file)
                logger.info(f"self.whr.file_bext_export completed for ({wav_file})")

                self.whr.file_info_import(wav_file, self.engineer_name)
                logger.info(f"self.whr.file_info_import completed for ({wav_file})")

                self.cs.file_checksum_generate(wav_file)
                self.cs.write_checksum_to_file(wav_file, f"{wav_file}.md5")
                logger.info(f"New checksum generated for ({wav_file})")

    def generate_access_files(self):
        logger.info(f"generate_access_files started for {self.engineer_name}")

        print(self.ms.generate_access_files)
        for index, file in enumerate(self.staging_file_list):
            self.progress_bar(index, len(self.staging_file_list))
            if file.endswith(".wav"):
                wav_file = file
                self.pbo.get_shelfmark(wav_file)
                logger.info(f"self.pbo.get_shelfmark completed for ({wav_file})")

                self.pbo.access_file_generate(wav_file)
                logger.info(f"self.pbo.access_file_generate completed for ({wav_file})")

    def move_files_to_backup(self):
        logger.info(f"move_files_to_backup started for {self.engineer_name}")

        print(self.ms.move_files_to_backup)
        copy_location = os.path.join(self.ROOT_BACKUP, self.engineer_name)

        if os.path.exists(copy_location):
            logger.info(f"Directory exists at {copy_location}")
            pass
        else:
            os.mkdir(copy_location)
            logger.info(f"New directory created at {copy_location}")

        get_datetime = datetime.now().strftime("%Y%m%d_%H.%M")
        existing_batch_dir = os.listdir(copy_location)

        if existing_batch_dir != []:
            number = len(existing_batch_dir) + 1
            batch_dir_number = f"batch_{number:02}_{get_datetime}"
        else:
            batch_dir_number = f"batch_01_{get_datetime}"

        self.batch_copy = os.path.join(copy_location, batch_dir_number)
        os.mkdir(self.batch_copy)
        logger.info(f"New batch directory created at {self.batch_copy}")

        for index, staged_file in enumerate(self.staging_file_list):
            self.progress_bar(index, len(self.staging_file_list))
            shutil.move(staged_file, self.batch_copy)
            logger.info(f"{staged_file} moved to {self.batch_copy}")
            if os.path.exists(f"{staged_file}.md5"):
                shutil.move(f"{staged_file}.md5", self.batch_copy)
            else:
                pass


### start backup service
bfs = BackupFileService()
logger.info("Backup service started")

### clear staging area
bfs.clear_staging_area()

### source copy set and engineer name captured
try:
    bfs.set_source_and_engineer()
except ValueError as e:
    Prompt.ask(str(e))
    exit()

if bfs.engineer_name == bfs.BAU_ENGINEER_1 or bfs.engineer_name == bfs.BAU_ENGINEER_2:
    try:
        dmo = DriveMirror(bfs.source_directory, bfs.ROOT_BACKUP, bfs.engineer_name)
        dmo.run_drive_mirror_operations()  # move operations to drive mirror service
    except Exception as e:
        logger.warning(f"Error mirroring drive: {e}")
        print(f"Error mirroring drive: {e}")
        exit()

    Prompt.ask(
        "\n[bold magenta][u]Drive mirror complete![/u][/bold magenta]. [bold]Please eject the drive[/bold]"
    )

else:
    ### copy files to staging area
    try:
        bfs.copy_files_to_staging()
    except ValueError as e:
        Prompt.ask(str(e))
        bfs.clear_staging_area()
        exit()

    ### eject drive
    bfs.drive_eject_request()

    ### checksums deleted, file info written, new checksums written
    bfs.post_copy_operations()

    try:
        bfs.generate_access_files()
    except Exception as e:
        logger.warning(f"Error generating access files: {e}")
        print(f"Error generating access files: {e}")

    ## move files to backup area
    bfs.move_files_to_backup()

    Prompt.ask("[bold magenta][u]Backup complete![/u][/bold magenta]")
