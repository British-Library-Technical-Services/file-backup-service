"""User-facing rich text messages and prompts for the file backup & drive mirror services.

This module centralises formatted console messages (Rich markup) and small helper
methods that return dynamic text shown during backup or mirroring workflows.
Import and instantiate MessagingService where interactive CLI messaging is needed.
"""
import os
from rich import print


class MessagingService:

    welcome_messgage = """

----| [bold magenta][u]Welcome to the File Backup Service for Offline Digital Preservation[/u][/bold magenta] |----

Before starting the service please ensure the files you'd like to backup are [bold]stored in a directory named after yourself[/bold]:

[bold][External USB Drive][/bold]
 |---- [Carlo Krahmer]
    |---- *.wav
    |---- *.md5
    |---- *_ExcelBatchUpload.xlsx
    |---- *.json

Files and directories outside of the named folder will be ignored.

Press [bold magenta]any key[/bold magenta] to start the service and navigate to the root of the directory location:"""

    collection_backup_message = """
[bold magenta][u]Backup Service Criteria[/u][/bold magenta]

[bold]Please ensure the following criteria is correct before starting the service:[/bold]

1. The files for backup are organised in a single directory
2. The directory is in the root of the drive with no subdirectories
3. All the audio files have .md5 checksums
4. The directory contains your batch SIP spreadsheet, [bold]named in the following format[/bold]:

---------------------------------------------------------------------------------------------------
| EnigneerName_Date_BatchNo_ExcelBatchUpload     | CarloKrahmer_240307_1_ExcelBatchUpload.xlsx    |
---------------------------------------------------------------------------------------------------

5. A .json file for each unique set of Process Metadata listed in the batch SIP spreadsheet
6. Ensure all tracking data is up to date in the collection tracking spreadsheet on MS365
\n"""

    confirm_checks = "[bold]Press any key to continue[/bold]"
    user_cancel = (
        "[bold][red]Warning[/red]. User cancelled the operation. Exiting.[/bold]"
    )
    empty_directory = "[bold][red]Warning[/red]. No directories found. Exiting[/bold]"
    no_engineer_match = "[bold][red]Warning[/red]. Directory name does not match any engineer name in the list[/bold].  \nPlease check the name matches and that you are opening the root location containing the named directory (not the directory itself). \n[bold]The service will EXIT. Press any key[/bold]"
    no_files_found = "[bold][red]Warning[/red]. No files found in the directory[/bold].  \nPlease check the directory and try again. \n[bold]The service will EXIT. Press any key[/bold]"
    batch_sip_spreadsheet_missing = "[bold][red]Warning[/red]. Batch SIP spreadsheet missing[/bold]. \nPlease add to the directory with the files.  \n[bold]The service will EXIT. Press any key[/bold]"
    checksum_fail = "[bold][red]Warning Checksum verification failed[/red]. See log for details[/bold]. \nFiles will be removed from the staging area. Please check the files and try again. \n[bold]The service will EXIT. Press any key[/bold]."
    checksum_pass = "[bold][green]Checksum verification passed[/green]. File processing will begin.[/bold]"

    eject_drive = "\n==| [bold]YOUR DRIVE IS SAFE TO EJECT[/bold] |==\n"

    copy_files_to_staging = (
        "[bold magenta]1.Copying files[/bold magenta]  to staging area..."
    )
    post_copy_operations = "[bold magenta]2. Post copy[/bold magenta] operations..."
    generate_access_files = (
        "[bold magenta]3. Generating access files[/bold magenta] ..."
    )
    move_files_to_backup = (
        "[bold magenta]4. Moving files[/bold magenta] to backup location..."
    )

    def engineer_file_data(self, engineer, file_list):
        # file_list = [file for file in file_list if not file.endswith('.md5')]
        os.system("cls||clear")
        return f"""
Hello [bold magenta]{engineer}![/bold magenta] {len(file_list)} files will be backed-up today.

This may take some time - once the files are copied to the staging area further opertations will be 
carried out but you do not need to present for these.

[bold]Please eject the drive when asked[/bold] and leave the service to complete
the backup.

To view the backup criteria before starting, please press "v".  Otherwise [bold]Press Enter[/bold] to start the service
"""

    def drive_mirror_message(self, engineer):
        os.system("cls||clear")
        return f"""
Hello [bold magenta]{engineer}![/bold magenta]. Your drive will be mirrored in the backup location.

This may take some time, the service will inform you when it completes and it is safe to remove the drive.
"""

    view_or_run = 'To view the list of files, press [bold yellow]"v"[/bold yellow] or press [bold magenta]any other key[/bold magenta] to start the mirror service'
