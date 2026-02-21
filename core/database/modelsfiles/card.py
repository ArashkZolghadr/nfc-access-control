"""
Card Model
==========
Manages NFC cards, security, and validation
"""
from datetime import datetime
import hashlib
import secrets
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from core.database.corefiles.base import Base
from core.database.corefiles.enums import CardStatus


class Card(Base):
    """
    NFC Card model
    Handles card information, encryption, and access validation
    """
    __tablename__ = 'cards'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Card Identifiers (encrypted)
    uid = Column(String(255), unique=True, nullable=False, index=True)
    uid_hash = Column(String(64), unique=True, nullable=False, index=True)
    
    # Card Information
    card_number = Column(String(50), unique=True, nullable=True, index=True)
    card_type = Column(String(50), default="RFID", nullable=False)
    batch_number = Column(String(50), nullable=True)
    serial_number = Column(String(100), nullable=True)
    
    # User Association
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Status and Validity
    status = Column(SQLEnum(CardStatus), default=CardStatus.ACTIVE, nullable=False, index=True)
    issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    activated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    
    # Security
    is_encrypted = Column(Boolean, default=True, nullable=False)
    encryption_key = Column(String(255), nullable=True)
    security_code = Column(String(10), nullable=True)
    
    # Usage Tracking
    total_uses = Column(Integer, default=0, nullable=False)
    failed_attempts = Column(Integer, default=0, nullable=False)
    last_failed_attempt = Column(DateTime, nullable=True)
    
    # Physical Card Info
    physical_condition = Column(String(50), default="good", nullable=False)
    replacement_card_id = Column(Integer, ForeignKey('cards.id', ondelete='SET NULL'), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_used = Column(DateTime, nullable=True, index=True)
    
    # Additional Info
    notes = Column(Text, nullable=True)
    issue_reason = Column(String(255), nullable=True)
    revocation_reason = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="cards", foreign_keys=[user_id])
    access_logs = relationship("AccessLog", back_populates="card", cascade="all, delete-orphan", lazy='dynamic')
    replacement = relationship("Card", remote_side=[id], uselist=False)

    def __repr__(self):
        return f"<Card(id={self.id}, number='{self.card_number}', status={self.status.value})>"

    def __str__(self):
        return f"Card {self.card_number or self.uid_hash[:8]}"

    # Static Methods
    
    @staticmethod
    def hash_uid(uid: str) -> str:
        """Hash UID using SHA-256"""
        return hashlib.sha256(uid.encode()).hexdigest()
    
    @staticmethod
    def generate_card_number(prefix: str = "NFC") -> str:
        """Generate unique card number"""
        random_part = secrets.token_hex(6).upper()
        timestamp = datetime.utcnow().strftime("%y%m")
        return f"{prefix}-{timestamp}-{random_part}"
    
    @staticmethod
    def generate_security_code() -> str:
        """Generate 6-digit security code"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    # Properties
    
    @property
    def is_expired(self) -> bool:
        """Check if card has expired"""
        if not self.expires_at:
            return False
        return self.expires_at < datetime.utcnow()
    
    @property
    def days_until_expiry(self) -> int:
        """Get days until card expires"""
        if not self.expires_at:
            return 999999
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.days)
    
    @property
    def is_blocked(self) -> bool:
        """Check if card is in blocked status"""
        blocked_statuses = [CardStatus.LOST, CardStatus.STOLEN, CardStatus.SUSPENDED]
        return self.status in blocked_statuses
    
    # Validation Methods
    
    def is_valid(self) -> bool:
        """Check if card is valid for use"""
        if self.status != CardStatus.ACTIVE:
            return False
        
        if self.is_expired:
            return False
        
        if not self.user.is_active:
            return False
        
        return True
    
    def check_access(self, zone=None) -> tuple[bool, str]:
        """
        Validate card access
        
        Args:
            zone: Zone object to check access for
            
        Returns:
            tuple: (access_granted, reason)
        """
        # Check card status
        if self.status != CardStatus.ACTIVE:
            if self.status == CardStatus.EXPIRED or self.is_expired:
                return False, "Card has expired"
            elif self.status == CardStatus.LOST:
                return False, "Card reported as lost"
            elif self.status == CardStatus.STOLEN:
                return False, "Card reported as stolen"
            elif self.status == CardStatus.SUSPENDED:
                return False, "Card is suspended"
            elif self.status == CardStatus.DAMAGED:
                return False, "Card is damaged"
            else:
                return False, f"Card is {self.status.value}"
        
        # Check user status
        if not self.user.is_active:
            return False, "User account is inactive"
        
        if not self.user.is_employed:
            return False, "User employment terminated"
        
        # Check zone access if provided
        if zone:
            if not self.user.has_zone_access(zone.id):
                return False, f"No access to zone: {zone.name}"
        
        # All checks passed
        return True, "Access granted"
    
    # Action Methods
    
    def activate(self):
        """Activate the card"""
        self.status = CardStatus.ACTIVE
        self.activated_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def suspend(self, reason: str = None):
        """Suspend the card"""
        self.status = CardStatus.SUSPENDED
        if reason:
            self.revocation_reason = reason
        self.updated_at = datetime.utcnow()
    
    def report_lost(self):
        """Mark card as lost"""
        self.status = CardStatus.LOST
        self.revocation_reason = "Reported lost by user"
        self.updated_at = datetime.utcnow()
    
    def report_stolen(self):
        """Mark card as stolen"""
        self.status = CardStatus.STOLEN
        self.revocation_reason = "Reported stolen by user"
        self.updated_at = datetime.utcnow()
    
    def mark_damaged(self):
        """Mark card as damaged"""
        self.status = CardStatus.DAMAGED
        self.physical_condition = "damaged"
        self.updated_at = datetime.utcnow()
    
    def expire(self):
        """Expire the card"""
        self.status = CardStatus.EXPIRED
        if not self.expires_at:
            self.expires_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_usage(self):
        """Update usage statistics"""
        self.total_uses += 1
        self.last_used = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def record_failed_attempt(self):
        """Record a failed access attempt"""
        self.failed_attempts += 1
        self.last_failed_attempt = datetime.utcnow()
        
        # Auto-suspend after too many failed attempts
        if self.failed_attempts >= 5:
            self.suspend("Too many failed access attempts")
    
    def reset_failed_attempts(self):
        """Reset failed attempt counter"""
        self.failed_attempts = 0
        self.last_failed_attempt = None
    
    def replace_with(self, new_card_id: int):
        """Mark this card as replaced by another"""
        self.status = CardStatus.INACTIVE
        self.replacement_card_id = new_card_id
        self.revocation_reason = f"Replaced with card #{new_card_id}"
        self.updated_at = datetime.utcnow()
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert card to dictionary"""
        data = {
            'id': self.id,
            'card_number': self.card_number,
            'card_type': self.card_type,
            'status': self.status.value,
            'user_id': self.user_id,
            'issued_at': self.issued_at.isoformat() if self.issued_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'total_uses': self.total_uses,
            'is_valid': self.is_valid(),
            'days_until_expiry': self.days_until_expiry
        }
        
        if include_sensitive:
            data.update({
                'uid': self.uid,
                'uid_hash': self.uid_hash,
                'security_code': self.security_code,
                'failed_attempts': self.failed_attempts,
                'notes': self.notes
            })
        
        return data
