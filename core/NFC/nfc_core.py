"""
NFC Core Hardware Abstraction Layer
Path: core/NFC/nfc_core.py

Handles low-level communication with NFC readers (e.g., via pyscard or nfcpy).
Decoupled from database logic.
"""

import time
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class NFCReader:
    """
    Base class for interacting with physical NFC readers.
    """
    
    def __init__(self, device_path: str = None, use_mock: bool = False):
        """
        Initialize the NFC Reader.
        
        Args:
            device_path: Optional path to the hardware device (e.g., USB port).
            use_mock: If True, uses simulated hardware for testing.
        """
        self.device_path = device_path
        self.use_mock = use_mock
        self.is_connected = False
        
        if not self.use_mock:
            self._init_hardware()
        else:
            logger.info("NFCReader initialized in MOCK mode.")
            self.is_connected = True

    def _init_hardware(self):
        """
        Initialize physical hardware connection.
        (Placeholder for actual pyscard/nfcpy implementation)
        """
        try:
            # Example using a conceptual hardware library:
            # import nfc
            # self.clf = nfc.ContactlessFrontend(self.device_path or 'usb')
            self.is_connected = True
            logger.info("Physical NFC reader connected successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize NFC hardware: {e}")
            self.is_connected = False

    def read_uid(self, timeout: int = 5) -> Optional[str]:
        """
        Read the UID of an NFC card presented to the reader.
        
        Args:
            timeout: How long to wait for a card in seconds.
            
        Returns:
            String representing the hex UID of the card, or None if timeout.
        """
        if self.use_mock:
            # Simulate waiting and reading a card
            logger.debug(f"Mock reader waiting for card (timeout {timeout}s)...")
            time.sleep(1) # Simulate delay
            # Return a mock UID for testing (can be changed dynamically)
            return "04:A1:B2:C3:D4:E5:F6"

        if not self.is_connected:
            logger.error("Cannot read UID: Reader is not connected.")
            return None

        # Placeholder for actual hardware read logic:
        # try:
        #     target = self.clf.connect(rdwr={'on-connect': lambda tag: False})
        #     if target:
        #         return target.identifier.hex().upper()
        # except Exception as e:
        #     logger.error(f"Error reading card: {e}")
        
        return None

    def start_listening(self, callback: Callable[[str], None], interval: float = 0.5):
        """
        Continuously listen for cards and trigger a callback when one is found.
        
        Args:
            callback: Function to call when a UID is read. Must accept UID string.
            interval: Delay between polling attempts.
        """
        logger.info("Started continuous NFC listening...")
        try:
            while True:
                uid = self.read_uid(timeout=1)
                if uid:
                    logger.debug(f"Card detected with UID: {uid}")
                    callback(uid)
                    # Sleep to prevent multiple reads of the same tap
                    time.sleep(2) 
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("NFC listening stopped by user.")
        finally:
            self.cleanup()

    def cleanup(self):
        """Release hardware resources."""
        if not self.use_mock:
            # self.clf.close()
            pass
        self.is_connected = False
        logger.info("NFCReader resources cleaned up.")
