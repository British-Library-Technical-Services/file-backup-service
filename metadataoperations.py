import subprocess

from logging_module import logger

class WavHeaderRewrite:

    def file_bext_export(self, wav_file):
        try:
            bext_data = subprocess.Popen(
                ["ffprobe", "-hide_banner", "-i", wav_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except Exception as e:
            logger.critical(f"Error exporting BEXT data for {wav_file}. {e}")
            raise ValueError(e)

        data_map = {
            "encoded_by": "encoded_by",
            "date": "date",
            "creation_time": "creation_time",
        }
        self.results = {
            "encoded_by": "",
            "date": "",
            "creation_time": "",
        }

        try:
            for data in bext_data.stdout.readlines():
                data = data.decode(encoding="utf-8").strip()
        except Exception as e:
            logger.critical(f"Error reading BEXT data for {wav_file}. {e}")
            raise ValueError(e)

        for key, value in data_map.items():
            if key in data:
                self.results[value] = data.split(":")[1].strip()

    def file_info_import(self, wav_file, engineer_name):

        if not (
            self.results["encoded_by"] == ""
            or self.results["date"] == ""
            or self.results["creation_time"] == ""
        ):
            isft = self.results["encoded_by"]
            icrd = f"{self.results['date']}T{self.results['creation_time'].replace('-', ':')}Z"

            try:
                subprocess.run(
                    [
                        "bwfmetaedit",
                        wav_file,
                        "--append",
                        "--Originator=" + "",
                        "--OriginationDate=" + "",
                        "--OriginationTime=" + "",
                        "--IARL=" + "GB, BL",
                        "--ICRD=" + icrd,
                        "--IENG=" + engineer_name,
                        "--ISFT=" + isft,
                    ],
                    stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL # mute subprocess output
                )
            except Exception as e:
                logger.critical(f"Error importing BEXT data for {wav_file}. {e}")
                raise ValueError(e)
        else:
            pass
