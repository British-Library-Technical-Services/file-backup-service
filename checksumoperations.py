import os
import hashlib
import glob


class ChecksumService:
    def __init__(self):
        self.file_checksum = None
        self.verfied_status = False
        self.failed_files = []

    def file_checksum_generate(self, file):
        file_hash = hashlib.md5()

        with open(file, "rb") as f:
            while chunk := f.read(8192):
                file_hash.update(chunk)

            self.file_checksum = file_hash.hexdigest()

    def write_checksum_to_file(self, file, md5_file_name):
        with open(md5_file_name, "w") as md5_file:
            md5_file.write(f"{self.file_checksum} *{os.path.basename(file)}")

    def file_checksum_verify(self, file):
        md5_file_name = f"{file}.md5"

        with open(md5_file_name, "r") as md5_file:
            md5_string = md5_file.read(32)
            if self.file_checksum == md5_string:
                self.verfied_status = True
            else:
                self.verfied_status = False
                self.failed_files.append(os.path.basename(file))

    def delete_exisiting_checksums(self, location):
        for file in glob.glob(location + "/*.md5"):
            os.remove(file)
