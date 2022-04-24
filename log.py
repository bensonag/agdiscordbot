from google.cloud import logging

class Logger():
    def __init__(self):
        self._logger = logging.Client().logger('AGWLDiscord')

    def info(self, log: str):
        print(log)
        self._logger.log_text(log, severity="INFO")
    
    def warning(self, log: str):
        print(log)
        self._logger.log_text(log, severity="WARNING")

    def error(self, log: str):
        print(log)
        self._logger.log_text(log, severity="ERROR")
