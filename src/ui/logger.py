import logging
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtGui import QColor

# Color codes for different log levels
LOG_COLORS = {
    logging.DEBUG: QColor(128, 128, 128),  # Gray
    logging.INFO: QColor(0, 0, 0),        # Black
    logging.WARNING: QColor(255, 165, 0), # Orange
    logging.ERROR: QColor(255, 0, 0),     # Red
    logging.CRITICAL: QColor(128, 0, 128) # Purple
}

class QTextEditLogger(logging.Handler):
    def __init__(self, text_edit: QTextEdit):
        super().__init__()
        self.text_edit = text_edit

    def emit(self, record):
        msg = self.format(record)
        color = LOG_COLORS.get(record.levelno, QColor(0, 0, 0))
        self.text_edit.setTextColor(color)
        self.text_edit.append(msg)

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    return logger