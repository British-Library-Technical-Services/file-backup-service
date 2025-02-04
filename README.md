# Offline Backup Service for Audio Preservation Data

This project provides an offline backup service for audio preservation data. It ensures that audio files are backed up, checksums are verified, and access files are generated.

## Features

- Backup audio files from a source directory to a staging area
- Verify checksums of audio files
- Rewrite BWF Header data
- Generate access files in m4a format
- Move files to a backup location
- Mirror drives for specific engineers

## Requirements

- Python 3.x
- `dotenv` package
- `rich` package
- `tkinter` package
- `ffprobe`, `ffmpeg` and `bwfmetaedit` executables

## Installation

1. Clone the repository:
    ```sh
    git clone <https://github.com/British-Library-Technical-Services/file-backup-service.git>
    cd <file-backup-service>
    ```

2. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

3. Set up the environment variables in the [.env](http://_vscodecontentref_/0) file:
    ```env
    ROOT_LOCATION=<path-to-root-location>
    DIR_SELECT=<path-to-directory-selection>
    STAGING_LOCATION=<path-to-staging-location>
    ROOT_BACKUP=<path-to-root-backup>
    MSO_STORE=<path-to-mso-store>
    BAU_ENGINEER_1=<engineer-name-1>
    BAU_ENGINEER_2=<engineer-name-2>
    ```

## Usage

1. Run the backup service:
    ```sh
    python3 backupservice.py
    ```

2. Follow the prompts to select the source directory and start the backup process.

## Documentation

For detailed documentation on the usage of this service, see [here](https://british-library-technical-services.github.io/Documentation/docs/digital_preservation/backup_service.html).