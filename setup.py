import logging
import os
import subprocess
import sys

import nltk

TEMP_PATH = 'temp'
PROFILE_PATH = 'profile'
LICHESS_URL = "https://database.lichess.org/lichess_db_puzzle.csv.zst"
LICHESS_PATH = "data/lichess_db_puzzle.csv"
NLTK_MODULES = [
    'wordnet',
    'brown',
    'averaged_perceptron_tagger'
]

def pip_install(package:str):
    subprocess.run([sys.executable,'-m','pip','install',package],check=True)

setup_logger = logging.Logger("SETUP",level=logging.INFO)
setup_logger.addHandler(logging.StreamHandler())

def setup():
    if not os.path.isdir(TEMP_PATH):
        setup_logger.warning(f"Temp directory not found! making {TEMP_PATH}")
        os.mkdir(TEMP_PATH)
    if not os.path.isdir(PROFILE_PATH):
        setup_logger.warning(f"Profile directory not found! making {PROFILE_PATH}")
        os.mkdir(PROFILE_PATH)
    if not os.path.isfile(LICHESS_PATH):
        setup_logger.warning(f"File {LICHESS_PATH} not found!")
        setup_logger.info("Importing required libraries...")
        pip_install('zstandard')#install only if needed, as not actually required for the main program
        from io import BytesIO
        from urllib.request import urlopen

        import zstandard  #type:ignore
        dctx = zstandard.ZstdDecompressor()
        setup_logger.info(f"Opening url {LICHESS_URL}...")
        url = urlopen(LICHESS_URL)
        setup_logger.info("Opened url. Downloading file...")
        in_stream = BytesIO(url.read())
        out_stream = open(LICHESS_PATH,'wb')
        setup_logger.info("Downloaded file and opened in and out streams. Decompressing and writing...")
        dctx.copy_stream(in_stream,out_stream)
        out_stream.close()
        setup_logger.info(f"Successfully downloaded {LICHESS_PATH}.")
    setup_logger.info("Downloading/updating for NLTK modules.")
    for module in NLTK_MODULES:
        nltk.download(module)


if __name__ == '__main__':
    setup()