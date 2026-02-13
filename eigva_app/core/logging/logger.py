import logging
from logging.handlers import TimedRotatingFileHandler
import os

LOG_DIR = "logs"
LOG_FILE = "app_errors.log"

# Sukuriame katalogą, jei neegzistuoja
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)  # galima pakeisti į DEBUG jei reikia

# Handler, kuris sukuria naują log failą kas nurodytą laiką
handler = TimedRotatingFileHandler(
    filename=os.path.join(LOG_DIR, LOG_FILE),
    when="D",            # kas dieną naujas failas
    interval=1,          # kas 1 dieną
    backupCount=30,      # laikyti paskutines 30 dienų
    encoding="utf-8"
)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
handler.setFormatter(formatter)

logger.addHandler(handler)