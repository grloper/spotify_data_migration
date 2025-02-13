import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def log(msg, level=logging.INFO):
    logging.log(level, msg)
