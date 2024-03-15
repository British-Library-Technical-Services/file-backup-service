import os


class MessagingService:

    welcome_message = """
[bold magenta][u]Welcome to the File Backup Service for Offline Digital Preservation[/u][/bold magenta]

[bold]Before starting, please check the following:[/bold]

    1. The files for backup are organised in a single directory
    2. The directory is in the root of the drive with no subdirectories
    3. The directory is named with your name (first and surname)
    4. All the audio files have .md5 checksums
    5. The directory contains your batch SIP and tracking spreadsheets:

        * Engineer_Date_BatchNo_ExcelBatchUpload.xlsx
        * Engineer_Date_BatchNo_TrackingSheet.xlsx

    6. The metadata for the all files in the directory is in the above spreadsheets\n"""

    confirm_checks = "Once the checks have been completed, [bold]please attach your drive and hit enter to continue[/bold]\n"
    user_cancel = (
        "[bold][red]Warning[/red]. User cancelled the operation. Exiting.[/bold]"
    )
    empty_directory = "[bold][red]Warning[/red]. No directories found. Exiting.[/bold]"
    no_engineer_match = "[bold][red]Warning[/red]. Directory name does not match any engineer name in the list.  Please check the directory name matches[/bold]"
    tracking_spreadsheet_missing = "[bold][red]Warning[/red]. Tracking spreadheet missing. Please add to the directory with the files. Exiting.[/bold]"
    batch_sip_spreadsheet_missing = "[bold][red]Warning[/red]. Batch SIP spreadsheet missing. Please add to the directory with the files. Exiting.[/bold]"
    checksum_fail = "[bold][red]Warning Checksum verification failed[/red]. See log for details. Files will be removed from the staging area. Please check the files and try again. Exiting."
    checksum_pass = "[bold][green]Checksum verification passed[/green]. File processing will begin.[/bold]"

    eject_drive = "==| [bold]DRIVE SAFE TO EJECT[/bold] |=="

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
        os.system("cls||clear")
        return f"""
Hello [bold magenta]{engineer}![/bold magenta] {len(file_list)} files will be backed-up today.

This may take some time - once the files are copied to the staging area further opertations will be 
carried out but you do not need to present for these.

[bold]Please eject the drive when asked[/bold] and leave the service to complete
the backup.

[bold]Press enter[/bold] to start the service
"""
