import os
import glob
import subprocess
import shutil
import yagmail
from dotenv import load_dotenv


class PostBackupOperations:
    def __init__(self, staging_location):
        self.MSO_STORE = r"/path/to/_mso_audio"
        self.collection_no = None
        self.STAGING_LOCATION = staging_location
        self.m4a_file = None

    def get_shelfmark(self, wav_file):
        self.wav_file_name = os.path.basename(wav_file.split(".")[0])
        parsed_name = self.wav_file_name.split("_")
        if parsed_name[1].startswith(("1", "2", "9")):
            self.collection_no = parsed_name[1][0:3]
        elif parsed_name[1].startswith("C"):
            self.collection_no = parsed_name[1].split("-")[0]
        else:
            self.collection_no = parsed_name[1]

    def move_to_mso_store(self):
        collection_directory = os.path.join(self.MSO_STORE, self.collection_no)
        if not os.path.exists(collection_directory):
            os.mkdir(collection_directory)
            shutil.move(self.m4a_file, collection_directory)
        else:
            if os.path.exists(os.path.join(collection_directory, self.m4a_file)):
                os.remove(os.path.join(self.STAGING_LOCATION, self.m4a_file))

    def access_file_generate(self, wav_file):
        wav_file_name = os.path.basename(wav_file.split(".")[0])
        self.m4a_file = os.path.join(self.STAGING_LOCATION, f"{wav_file_name}.m4a")
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
                self.m4a_file,
            ]
        )
        self.move_to_mso_store()

    def send_tracking_spreadsheet(self, engineer_name, batch_location, tracking_sheet):
        load_dotenv()
        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_PASSWORD")
        recepieint_email = os.getenv("RECEPIENT_EMAIL")

        yag = yagmail.SMTP(sender_email, sender_password)
        yag.send(
            to=recepieint_email,
            subject=f"Engineer: {engineer_name}, Tracking Sheet: {tracking_sheet})",
            contents=f"Tracking Spreadhsheet located in {batch_location}",
            attachments=os.path.join(batch_location, tracking_sheet),
        )
