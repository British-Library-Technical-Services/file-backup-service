import logging
from rich import print
from rich.prompt import Prompt
import os
import tkinter as tk
from tkinter import filedialog
from datetime import datetime
import glob
import shutil

from messageoperations import MessagingService
import userlist
from checksumoperations import ChecksumService
from metadataoperations import WavHeaderRewrite
from postoperations import PostBackupOperations
from progressbar import progress_bar

logTS = datetime.now().strftime("%Y%m%d_%H.%M_log.log")
root_location = r"/path/to/.logs"
log = os.path.join(root_location, logTS)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s:%(module)s:%(levelname)s:%(message)s")
file_handler = logging.FileHandler(log)

file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)


class BackupFileService:
    def __init__(self):

        self.STAGING_LOCATION = r"/path/to/_staging_area"
        self.ROOT_BACKUP = r"/path/to/_backup_storage"

        self.source_directory = None
        self.collection_no = None
        self.engineer_name = None
        self.fco = ChecksumService()
        self.whr = WavHeaderRewrite()
        self.pbo = PostBackupOperations(self.STAGING_LOCATION)
        self.progress_bar = progress_bar
        self.staging_file_list = None
        self.batch_copy = None
        self.ms = MessagingService()

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

        print(self.ms.welcome_message)
        Prompt.ask(self.ms.confirm_checks)

        source_drive_select = filedialog.askdirectory()
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

    def copy_files_to_staging(self):
        logger.info(f"copy_files_to_staging started for {self.engineer_name}")

        file_list = glob.glob(self.source_directory + "/*.*")
        if not any("_TrackingSheet.xlsx" in file for file in file_list):
            logger.warning(f"Tracking spreadsheet missing. Exiting.")
            raise ValueError(self.ms.tracking_spreadsheet_missing)

        elif not any("_ExcelBatchUpload.xlsx" in file for file in file_list):
            logger.warning(f"Batch SIP spreadsheet missing. Exiting.")
            raise ValueError(self.ms.batch_sip_spreadsheet_missing)
        else:
            Prompt.ask(self.ms.engineer_file_data(self.engineer_name, file_list))

            print(self.ms.copy_files_to_staging)

            for file in file_list:
                self.progress_bar(file_list.index(file), len(file_list))
                staging_file_copy = os.path.join(
                    self.STAGING_LOCATION, os.path.basename(file)
                )
                if file.endswith(".md5"):
                    pass
                elif file.endswith(".wav"):
                    md5_file_name = f"{file}.md5"

                    if os.path.exists(md5_file_name):
                        self.fco.file_checksum_generate(file)
                    else:
                        self.fco.file_checksum_generate(file)
                        self.fco.write_checksum_to_file(file, md5_file_name)
                        logger.info(f"Generated checksum for {file}")

                    shutil.copy2(file, staging_file_copy)
                    logger.info(f"{file} copied to staging area")

                    shutil.copy2(md5_file_name, f"{staging_file_copy}.md5")
                    logger.info(f"{md5_file_name} copied to staging area")

                    self.fco.file_checksum_verify(staging_file_copy)
                    logger.info(f"Checksum verification check for {staging_file_copy}")
                else:
                    shutil.copy2(file, staging_file_copy)
                    logger.info(f"{file} copied to staging area")

            if self.fco.failed_files != []:
                logger.critical(
                    f"Checksum verification failed for {self.fco.failed_files}"
                )
                raise ValueError(
                    f"""
{self.ms.checksum_fail}
Failed Files: {len(self.fco.failed_files)}; {self.fco.failed_files}"""
                )
            else:
                print(self.ms.checksum_pass)
                logger.info(f"Checksum verification passed for all files")

    def drive_eject_request(self):
        while os.path.exists(self.source_directory):
            Prompt.ask(self.ms.eject_drive)

        logger.info(f"{self.source_directory} ejected drive")

    def post_copy_operations(self):
        logger.info(f"post_copy_operations started for {self.engineer_name}")

        print(self.ms.post_copy_operations)

        self.fco.delete_exisiting_checksums(self.STAGING_LOCATION)
        logger.info(f"Deleted existing checksums in {self.STAGING_LOCATION}")

        self.staging_file_list = glob.glob(self.STAGING_LOCATION + "/*.*")

        for file in self.staging_file_list:
            self.progress_bar(
                self.staging_file_list.index(file), len(self.staging_file_list)
            )
            if file.endswith(".wav"):
                wav_file = file
                self.whr.file_bext_export(wav_file)
                logger.info(f"self.whr.file_bext_export completed for ({wav_file})")

                self.whr.file_info_import(wav_file, self.engineer_name)
                logger.info(f"self.whr.file_info_import completed for ({wav_file})")

                self.fco.file_checksum_generate(wav_file)
                self.fco.write_checksum_to_file(wav_file, f"{wav_file}.md5")
                logger.info(f"New checksum generated for ({wav_file})")

    def generate_access_files(self):
        logger.info(f"generate_access_files started for {self.engineer_name}")

        print(self.ms.generate_access_files)
        for file in self.staging_file_list:
            self.progress_bar(file.index(file), len(self.staging_file_list))
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

        for staged_file in self.staging_file_list:
            self.progress_bar(
                self.staging_file_list.index(staged_file), len(self.staging_file_list)
            )
            shutil.move(staged_file, self.batch_copy)
            logger.info(f"{staged_file} moved to {self.batch_copy}")
            if os.path.exists(f"{staged_file}.md5"):
                shutil.move(f"{staged_file}.md5", self.batch_copy)
            else:
                pass

    def email_tracking_sheet(self):
        logger.info(f"email_tracking_sheet started for {self.engineer_name}")
        tracking_sheet = [
            f for f in self.staging_file_list if f.endswith("_TrackingSheet.xlsx")
        ]
        self.pbo.send_tracking_spreadsheet(
            self.engineer_name, self.batch_copy, tracking_sheet[0].split("\\")[-1]
        )
        logger.info(f"Tracking sheet sent for {self.engineer_name} batch")


### start backup service
bfs = BackupFileService()
logger.info("Backup service started")

### clear staging area
bfs.clear_staging_area()

### source copy set and engineer name captured
try:
    bfs.set_source_and_engineer()
except ValueError as e:
    print(e)
    exit()

### copy files to staging area
try:
    bfs.copy_files_to_staging()
except ValueError as e:
    print(e)
    bfs.clear_staging_area()
    exit()

### eject drive
bfs.drive_eject_request()

### checksums deleted, file info written, new checksums written
bfs.post_copy_operations()
bfs.generate_access_files()

### move files to backup area
bfs.move_files_to_backup()
bfs.email_tracking_sheet()
print("[bold magenta][u]Backup complete![/u][/bold magenta]")
