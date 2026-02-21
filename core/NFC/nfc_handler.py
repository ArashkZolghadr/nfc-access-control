"""
NFC Handler and Business Logic Controller
Path: core/NFC/nfc_handler.py

Bridges the hardware layer with the database models.
Processes taps, validates policies, and logs access attempts.
"""

import logging
from sqlalchemy.orm import Session
from datetime import datetime

# Importing Enums and Base configurations
from core.database.corefiles.enums import AccessStatus

# Importing Models
from core.database.modelsfiles.card import Card
from core.database.modelsfiles.zone import Zone
from core.database.modelsfiles.user import User
from core.database.modelsfiles.access_log import AccessLog

logger = logging.getLogger(__name__)

class NFCHandler:
    """
    Handles the business logic for NFC card taps.
    Evaluates users, cards, zones, and policies to grant or deny access.
    """

    def __init__(self, db_session: Session):
        """
        Initialize handler with a database session.
        
        Args:
            db_session: SQLAlchemy active session.
        """
        self.session = db_session

    def process_tap(self, raw_uid: str, zone_id: int, device_id: str = None) -> dict:
        """
        Main function to process a card tap.
        
        Args:
            raw_uid: The raw UID read from the NFC hardware.
            zone_id: The ID of the zone/door where the tap occurred.
            device_id: (Optional) Identifier of the reader device.
            
        Returns:
            dict: Containing 'success' (bool), 'status' (AccessStatus value), and 'message' (str).
        """
        start_time = datetime.utcnow()
        decision_reason = ""
        access_status = AccessStatus.DENIED
        
        # 1. Clean and hash the UID
        clean_uid = raw_uid.replace(":", "").upper().strip()
        uid_hash = Card.hash_uid(clean_uid)

        # 2. Fetch the Card and Zone from DB
        card = self.session.query(Card).filter(Card.uid_hash == uid_hash).first()
        zone = self.session.query(Zone).filter(Zone.id == zone_id).first()

        try:
            # --- Validation Phase ---
            
            # Step A: Validate Zone existence
            if not zone:
                access_status = AccessStatus.INVALID_ZONE
                decision_reason = f"Zone ID {zone_id} does not exist."
                return self._finalize_attempt(clean_uid, access_status, decision_reason, card, zone, device_id, start_time)

            # Step B: Validate Card existence
            if not card:
                access_status = AccessStatus.INVALID_CARD
                decision_reason = "Unregistered or invalid card."
                return self._finalize_attempt(clean_uid, access_status, decision_reason, card, zone, device_id, start_time)

            # Step C: Use Card Model's built-in validation (Checks Card Status, Expiry, User Status, User Zone Access)
            is_card_valid, card_reason = card.check_access(zone=zone)
            if not is_card_valid:
                # Map reason to appropriate AccessStatus
                access_status = self._map_reason_to_status(card_reason, card)
                decision_reason = card_reason
                return self._finalize_attempt(clean_uid, access_status, decision_reason, card, zone, device_id, start_time)

            # Step D: Use Zone Model's built-in validation (Checks Capacity, Active status, Restictions, Operating hours)
            can_enter_zone, zone_reason = zone.can_enter(user=card.user)
            if not can_enter_zone:
                access_status = AccessStatus.INVALID_TIME if "closed" in zone_reason.lower() else AccessStatus.DENIED
                decision_reason = zone_reason
                return self._finalize_attempt(clean_uid, access_status, decision_reason, card, zone, device_id, start_time)

            # Step E: (Optional) If you have active policies, you would check them here.
            # active_policies = zone.get_active_policies()
            # for policy in active_policies:
            #     policy_pass, p_reason = policy.check_access(user=card.user)
            #     if not policy_pass: ...

            # --- Access Granted Phase ---
            access_status = AccessStatus.GRANTED
            decision_reason = "Access Granted"
            
            # Update entity statistics (using built-in model methods)
            card.update_usage()
            card.reset_failed_attempts()
            card.user.update_last_access()
            zone.increment_occupancy()
            
            return self._finalize_attempt(clean_uid, access_status, decision_reason, card, zone, device_id, start_time)

        except Exception as e:
            logger.error(f"Error processing tap for UID {raw_uid}: {str(e)}")
            self.session.rollback()
            return {"success": False, "status": AccessStatus.DENIED.value, "message": "Internal Server Error"}

    def _finalize_attempt(self, uid: str, status: AccessStatus, reason: str, 
                          card: Card, zone: Zone, device_id: str, start_time: datetime) -> dict:
        """
        Helper method to log the attempt to the database and commit changes.
        """
        decision_time = (datetime.utcnow() - start_time).total_seconds() * 1000  # in ms
        
        # Handle failed attempts on known cards
        if not status.is_success() and card:
            card.record_failed_attempt()

        # Create Access Log using the built-in class method
        try:
            log_entry = AccessLog.create_log(
                session=self.session,
                uid=uid,
                status=status,
                user_id=card.user_id if card else None,
                card_id=card.id if card else None,
                zone_id=zone.id if zone else None,
                reason=reason,
                device_id=device_id,
                decision_time_ms=decision_time,
                is_entry=True # Assuming entry tap; exit logic requires another parameter or state check
            )
            
            # Commit all changes (Logs, Card usage, Zone occupancy)
            self.session.commit()
            
            # Log to console/file
            log_msg = f"{status.value.upper()} | UID: {uid} | Zone: {zone.name if zone else 'Unknown'} | Reason: {reason}"
            if status.is_success():
                logger.info(log_msg)
            else:
                logger.warning(log_msg)

            return {
                "success": status.is_success(),
                "status": status.value,
                "message": reason,
                "log_id": log_entry.id,
                "user": card.user.full_name if card and card.user else "Unknown"
            }
            
        except Exception as e:
            logger.error(f"Failed to write access log: {e}")
            self.session.rollback()
            return {"success": False, "status": "error", "message": "Failed to log access"}

    def _map_reason_to_status(self, reason: str, card: Card) -> AccessStatus:
        """Helper to map string reasons from model validation to Enums."""
        reason_lower = reason.lower()
        if "expired" in reason_lower:
            return AccessStatus.EXPIRED
        elif "suspended" in reason_lower or "lost" in reason_lower or "stolen" in reason_lower:
            return AccessStatus.BLACKLISTED
        elif "inactive" in reason_lower:
            return AccessStatus.INACTIVE
        return AccessStatus.DENIED
