#!/usr/bin/env python3
import os
import time
import logging
import sys

class VoidLogger:
    """
    Zentrales Logging-System für VOID zur besseren Fehlersuche.
    Speichert Logs in ~/.void/void.log
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VoidLogger, cls).__new__(cls)
            cls._instance._setup()
        return cls._instance

    def _setup(self):
        # Log-Verzeichnis erstellen
        self.log_dir = os.path.expanduser("~/.void")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        self.log_file = os.path.join(self.log_dir, "void.log")
        
        # Logger konfigurieren
        self.logger = logging.getLogger("VOID")
        self.logger.setLevel(logging.DEBUG)
        
        # Datei-Handler (rotiert nicht, aber überschreibt bei jedem Start für Frische)
        # Oder wir hängen an mit Zeitstempel
        file_handler = logging.FileHandler(self.log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)
        
        # Formatierung
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(module)s: %(message)s', 
                                    datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.info("=== VOID Logger Initialisiert ===")
        self.logger.info(f"Plattform: {sys.platform}")
        self.logger.info(f"Python Version: {sys.version}")

    def debug(self, msg): self.logger.debug(msg)
    def info(self, msg): self.logger.info(msg)
    def warning(self, msg): self.logger.warning(msg)
    def error(self, msg): self.logger.error(msg)
    def critical(self, msg): self.logger.critical(msg)

def get_logger():
    return VoidLogger()

if __name__ == "__main__":
    log = get_logger()
    log.info("Test-Log Nachricht")
    print(f"Logs werden gespeichert in: {log.log_file}")
