# File Backup & Drive Mirror Service

A CLI-assisted workflow for offline audio preservation: stages and validates engineer digitisation batches, generates access derivatives, normalises select WAV metadata, commits files to a backup store, and optionally mirrors engineer drives incrementally.

---
## Table of Contents
1. Overview
2. Core Workflows
3. Architecture
4. Environment & Dependencies
5. Setup
6. Usage
7. File & Naming Conventions
8. Checksums
9. Metadata Normalisation
10. Access File Generation
11. Logging
12. Adding Engineers / Extra Drives
13. Troubleshooting
14. External Documentation

---
## 1. Overview
The service prevents data loss during ingest by ensuring:
- Only validated engineer batches enter long‑term storage.
- Files are checksum‑verified upon copy or update.
- Access (AAC) derivatives and standardised metadata are produced automatically.
- BAU Engineer drives can be mirrored quickly with change detection.

## 2. Core Workflows
### 2.1 Collection Backup
Steps:
1. User launches service and selects root of removable engineer drive.
2. Engineer directory is matched against the approved list (`userlist.py`).
3. Validation of batch contents (WAV + .md5, SIP spreadsheet, metadata JSON files).
4. Files copied to staging (`STAGING_LOCATION`).
5. Checksums verified (failures cause files to be removed from staging area and reported to user).
6. Optional WAV metadata extraction & rewrite (BEXT fields via ffprobe / bwfmetaedit).
7. AAC (.m4a) access copies generated and placed under `MSO_STORE/<collection_no>/`.
8. Originals moved to `ROOT_BACKUP` preserving structure.
9. Summary & safe‑eject message displayed.

### 2.2 BAU Engineer Drive Mirror
1. Scan source drive vs existing mirror tree.
2. Compute new / changed / removed file sets (size comparison).
3. Optional preview of changes before commit.
4. Copy or update files (copy sidecar .md5 if present).
5. Verify checksums for updated/new files; remove any failing pairs.
6. Remove source‑deleted files in mirror.
7. Display results.

## 3. Architecture
Module | Responsibility
-------|---------------
`backupservice.py` | Orchestrates collection backup workflow & user prompts
`drivemirroroperations.py` | Incremental mirroring (diff & apply)
`checksumoperations.py` | MD5 generation, writing, verification
`metadataoperations.py` | WAV metadata extraction + rewrite
`postoperations.py` | Access copy generation & placement
`messageoperations.py` | Centralised rich text messages
`logging_module.py` | Logging config (timestamped file per run)
`userlist.py` | Engineer directory whitelist

External tools: `ffmpeg` (inc. `ffprobe`), `bwfmetaedit`.

## 4. Environment & Dependencies
Python: see `requirements.txt`.
External executables must be on PATH:
- ffmpeg (provides ffprobe)
- bwfmetaedit

Environment variables (see `.env.example`):
```
ROOT_LOCATION        # Directory for log files
STAGING_LOCATION     # Temporary copy area
ROOT_BACKUP          # Final backup root
MSO_STORE            # Root for access copies (by collection)
BAU_ENGINEER_1       # Optional drive mirror base
BAU_ENGINEER_2       # Optional second drive
# BAU_ENGINEER_3 ... etc
```

## 5. Setup
```bash
git clone https://github.com/British-Library-Technical-Services/file-backup-service.git
cd file-backup-service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then edit values
```
Install external tools via your package manager (e.g. `apt install ffmpeg`).

## 6. Usage
Run interactive backup:
```bash
python backupservice.py
```
Follow prompts. Press "v" where offered to preview file changes (mirror workflow) or criteria.

## 7. File & Naming Conventions
Item | Convention
-----|-----------
Engineer directory | `Forename Surname` (case preserved)
Batch SIP spreadsheet | `EngineerName_YYMMDD_N_ExcelBatchUpload.xlsx`
Checksum sidecar | `<filename>.md5` (32 hex + space + *basename)
Access copy | `<original>.m4a`
Collection number parsing | From second token in WAV filename (logic in `PostBackupOperations.get_shelfmark`)

## 8. Checksums
- Service uses existing `.md5` where present; can generate & verify.
- Verification compares stored digest vs sidecar first 32 chars.
- Failures: file + sidecar deleted; listed to user + log.

## 9. Metadata Normalisation
- Extracted via `ffprobe` (fields: `encoded_by`, `date`, `creation_time`).
- Injected via `bwfmetaedit` (IARL, ICRD, IENG, ISFT). Empty originator fields reserved for future enrichment.

## 10. Access File Generation
- Codec: AAC
- Bitrate: 256k
- Command pattern: `ffmpeg -hide_banner -loglevel panic -y -i <wav> -c:a aac -b:a 256k -vn <out.m4a>`
- Stored under: `MSO_STORE/<collection_no>/`

## 11. Logging
- Log file created at startup: `<ROOT_LOCATION>/<YYYYMMDD_HH.MM_log.log>`
- Levels: INFO (operations), WARNING (recoverable), CRITICAL (failures)

## 12. Adding Engineers / Extra Drives
Edit `userlist.py` list. For extra physical drives for same engineer append numeric suffix: `Carlo Krahmer 2`.

## 13. Troubleshooting
Issue | Cause | Action
----- | ----- | ------
No engineer match | Directory name mismatch | Rename directory to approved format
Missing spreadsheet | Wrong name / absent | Ensure naming pattern + placement in engineer folder root
Checksum failures | Corrupted copy or wrong sidecar | Re-create sidecar or recopy from source
ffprobe/bwfmetaedit not found | Not installed / PATH | Install tools & relaunch
No changes (mirror) | Identical trees | Nothing to do; exit message normal

## 14. External Documentation
Further internal documentation: [Backup Service Docs](https://british-library-technical-services.github.io/Documentation/docs/digital_preservation/backup_service.html)
