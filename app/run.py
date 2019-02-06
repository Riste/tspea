import os
import sys
import logging
from app.tspea import worker
from app.tspea import master
from app.logconf import setup_logging
from app.tspea.utils import gen_out_dir_name

TYPE = os.getenv('TYPE', 'worker')
CITIES_FILE = os.getenv('CITIES_FILE', None)
BROKER_URL = os.getenv('BROKER_URL', None)
OUT_DIR = os.getenv('OUT_DIR', gen_out_dir_name())

setup_logging(OUT_DIR)
Log = logging.getLogger(__name__)

if __name__ == '__main__':
    if CITIES_FILE is None:
        Log.error('No problem file provided!')
        sys.exit(1)
    if BROKER_URL is None:
        Log.error('No message broker is specified!')
        sys.exit(1)
    if TYPE == 'worker':
        worker.run(CITIES_FILE, BROKER_URL)
    else:
        master.run(CITIES_FILE, BROKER_URL, OUT_DIR)
