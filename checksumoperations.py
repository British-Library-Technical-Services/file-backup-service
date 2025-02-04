import os
import hashlib
import glob

from logging_module import logger


class ChecksumService:
    def __init__(self):
        self.file_checksum = None
        self.verified_status = False
        self.failed_files = []

    def file_checksum_generate(self, file):
        try:
            file_hash = hashlib.md5()
            
            with open(file, "rb") as f:
                while chunk := f.read(8192):
                    file_hash.update(chunk)

                self.file_checksum = file_hash.hexdigest()
        except Exception as e:
            logger.critical(f"Error generating checksum for {file}. {e}")
            raise ValueError(e)

    def write_checksum_to_file(self, file, md5_file_name):
        try:
            with open(md5_file_name, "w") as md5_file:
                md5_file.write(f"{self.file_checksum} *{os.path.basename(file)}")
        except Exception as e:
            logger.critical(f"Error writing checksum to file {md5_file_name}. {e}")
            raise ValueError(e)

    def file_checksum_verify(self, file):
        md5_file_name = f"{file}.md5"

        try:
            with open(md5_file_name, "r") as md5_file:
                md5_string = md5_file.read(32)
        except Exception as e:
            logger.critical(f"Error reading checksum file {md5_file_name}. {e}")
            raise ValueError(e)
            
        if self.file_checksum == md5_string:
            self.verified_status = True
    
        else:
            self.verified_status = False
            self.failed_files.append(os.path.basename(file))

    def delete_exisiting_checksums(self, location):
        try:
            for file in glob.glob(location + "/*.md5"):
                os.remove(file)
        except Exception as e:
            logger.critical(f"Error deleting existing checksum files. {e}")
            raise ValueError(e)
