import logging
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

logTS = datetime.now().strftime("%Y%m%d_%H.%M_log.log")
ROOT_LOCATION = os.getenv("ROOT_LOCATION")
log = os.path.join(ROOT_LOCATION, logTS)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s:%(module)s:%(levelname)s:%(message)s")
file_handler = logging.FileHandler(log)

file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
