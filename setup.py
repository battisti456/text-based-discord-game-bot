import os
import logging
import nltk

LICHESS_URL = "https://database.lichess.org/lichess_db_puzzle.csv.zst"
LICHESS_PATH = "data/lichess_db_puzzle.csv"
NLTK_MODULES = [
    'wordnet',
    'brown'
]

setup_logger = logging.Logger("SETUP",level=logging.INFO)
setup_logger.addHandler(logging.StreamHandler())

def setup():
    if not os.path.isfile(LICHESS_PATH):
        setup_logger.warning(f"File {LICHESS_PATH} not found!")
        setup_logger.info(f"Importing required libraries...")
        import zstandard
        from io import BytesIO
        from urllib.request import urlopen
        dctx = zstandard.ZstdDecompressor()
        setup_logger.info(f"Opening url {LICHESS_URL}...")
        url = urlopen(LICHESS_URL)
        setup_logger.info(f"Opened url.")
        in_stream = BytesIO(url.read())
        out_stream = open(LICHESS_PATH,'wb')
        setup_logger.info("Opened in and out streams. Decompressing and writing...")
        dctx.copy_stream(in_stream,out_stream)
        out_stream.close()
        setup_logger.info(f"Successfully downloaded {LICHESS_PATH}.")
    setup_logger.info("Downloading/updating for NLTK modules.")
    for module in NLTK_MODULES:
        nltk.download(module)


if __name__ == '__main__':
    setup()