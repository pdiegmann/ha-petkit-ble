import logging

class Logger:
    def __init__(self):
        self.logger = logging.getLogger("PetkitW5BLEMQTT")
        logging.basicConfig(level=logging.DEBUG)
    
    def log_event(self, message):
        self.logger.info(message)
    
    def log_error(self, error):
        self.logger.error(error)