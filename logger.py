import logging
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtGui import QColor

# Color codes for different log levels
LOG_COLORS = {
    logging.DEBUG: QColor(150, 150, 150),    # Gray
    logging.INFO: QColor(0, 0, 255),         # Blue
    logging.WARNING: QColor(255, 165, 0),    # Orange
    logging.ERROR: QColor(255, 0, 0),        # Red
    logging.CRITICAL: QColor(128, 0, 128)    # Purple
}

class QTextEditLogger(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.widget.setReadOnly(True)
        
        # Configure the formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.setFormatter(formatter)

    def emit(self, record):
        # Ensure this method won't crash by handling all exceptions
        try:
            color = LOG_COLORS.get(record.levelno, QColor(0, 0, 0))  # Default to black
            msg = self.format(record)
            
            self.widget.setTextColor(color)
            self.widget.append(msg)
            
            # Safely scroll to bottom
            try:
                self.widget.verticalScrollBar().setValue(
                    self.widget.verticalScrollBar().maximum()
                )
            except:
                pass  # Ignore scrollbar errors
        except Exception as e:
            # Last resort fallback - print to console if logging widget fails
            print(f"Error in log widget: {str(e)}")
            print(f"Original log: {record.getMessage()}")

def setup_logger():
    # Set up the basic configuration for file logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='spotify_migration.log',
        filemode='a'
    )
    
    # Create console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    
    # Set lower log level for spotipy to see more details
    logging.getLogger('spotipy').setLevel(logging.DEBUG)
