import logging
import sys

def setup_logging(debug: bool = False):
    """Configures the root logger."""
    log_level = logging.DEBUG if debug else logging.INFO
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates if called multiple times
    # Useful if this function is called again or in testing scenarios
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)

    # Create formatter and add it to the handler
    formatter = logging.Formatter(log_format)
    ch.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(ch)

# You can get module-specific loggers in other files like this:
# import logging
# logger = logging.getLogger(__name__) 
# logger.info("This is an info message from my_module.")