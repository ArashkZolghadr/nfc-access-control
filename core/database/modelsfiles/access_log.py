"""
AccessLog Model
===============
Records all access attempts for audit and security
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Session

from core.database.corefiles.base import Base
from core.database.corefiles.enums import AccessStatus


class AccessLog(Base):
    """
    Access log model
    Records every access attempt (successful and failed) for audit trail
    """
    __tablename__ = 'access_logs'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Relationships (nullable for unknown/invalid attempts)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    card_id = Column(Integer, ForeignKey('cards.id', ondelete='SET NULL'), nullable=True, index=True)
    zone_id = Column(Integer, ForeignKey('zones.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Access Attempt Details
    uid_attempted = Column(String(255), nullable=False, index=True)
    status = Column(SQLEnum(AccessStatus), nullable=False, index=True)
    
    # Entry/Exit Tracking
    is_entry = Column(Boolean, default=True, nullable=False)
    exit_time = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Decision Details
    reason = Column(String(255), nullable=True)
    decision_time_ms = Column(Float, nullable=True)
    
    # Device Information
    device_id = Column(String(100), nullable=True, index=True)
    device_name = Column(String(100), nullable=True)
    device_location = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    # Additional Context
    user_agent = Column(String(255), nullable=True)
    request_method = Column(String(20), nullable=True)
    
    # Policy Information
    policy_id = Column(Integer, nullable=True)
    policy_applied = Column(String(100), nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Security Flags
    is_suspicious = Column(Boolean, default=False, nullable=False, index=True)
    is_emergency_override = Column(Boolean, default=False, nullable=False)
    alert_triggered = Column(Boolean, default=False, nullable=False)
    
    # Metadata (JSON stored as text)
    metadata_json = Column("metadata", Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="access_logs")
    card = relationship("Card", back_populates="access_logs")
    zone = relationship("Zone", back_populates="access_logs")

    def __repr__(self):
        return f"<AccessLog(id={self.id}, status={self.status.value}, time={self.timestamp})>"

    def __str__(self):
        user_info = f"User#{self.user_id}" if self.user_id else "Unknown"
        zone_info = f"Zone#{self.zone_id}" if self.zone_id else "Unknown"
        return f"{self.status.value} - {user_info} → {zone_info} @ {self.timestamp}"

    # Properties
    
    @property
    def is_success(self) -> bool:
        """Check if access was granted"""
        return self.status == AccessStatus.GRANTED
    
    @property
    def is_failure(self) -> bool:
        """Check if access was denied"""
        return not self.is_success
    
    @property
    def time_in_zone(self) -> str:
        """Get formatted time spent in zone"""
        if not self.exit_time or not self.duration_seconds:
            return "Still inside" if self.is_entry else "N/A"
        
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    
    @property
    def is_recent(self) -> bool:
        """Check if log is from last 24 hours"""
        return (datetime.utcnow() - self.timestamp) < timedelta(hours=24)
    
    @property
    def age_in_hours(self) -> float:
        """Get age of log entry in hours"""
        delta = datetime.utcnow() - self.timestamp
        return delta.total_seconds() / 3600
    
    # Class Methods
    
    @classmethod
    def create_log(cls, session: Session, uid: str, status: AccessStatus,
                   user_id: int = None, card_id: int = None, zone_id: int = None,
                   reason: str = None, device_id: str = None, **kwargs):
        """
        Create a new access log entry
        
        Args:
            session: SQLAlchemy session
            uid: Card UID that was attempted
            status: AccessStatus enum
            user_id: User ID (if known)
            card_id: Card ID (if known)
            zone_id: Zone ID (if applicable)
            reason: Reason for decision
            device_id: Device identifier
            **kwargs: Additional fields
            
        Returns:
            AccessLog: Created log entry
        """
        log = cls(
            uid_attempted=uid,
            status=status,
            user_id=user_id,
            card_id=card_id,
            zone_id=zone_id,
            reason=reason,
            device_id=device_id,
            timestamp=datetime.utcnow(),
            **kwargs
        )
        session.add(log)
        return log
    
    @classmethod
    def get_failed_attempts(cls, session: Session, hours: int = 24, limit: int = 100):
        """Get recent failed access attempts"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return session.query(cls).filter(
            cls.status != AccessStatus.GRANTED,
            cls.timestamp >= since
        ).order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def get_suspicious_activity(cls, session: Session, hours: int = 24):
        """Get logs marked as suspicious"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return session.query(cls).filter(
            cls.is_suspicious == True,
            cls.timestamp >= since
        ).order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def get_user_history(cls, session: Session, user_id: int, days: int = 30):
        """Get access history for specific user"""
        since = datetime.utcnow() - timedelta(days=days)
        return session.query(cls).filter(
            cls.user_id == user_id,
            cls.timestamp >= since
        ).order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def get_zone_activity(cls, session: Session, zone_id: int, hours: int = 24):
        """Get recent activity for specific zone"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return session.query(cls).filter(
            cls.zone_id == zone_id,
            cls.timestamp >= since
        ).order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def count_attempts_by_card(cls, session: Session, card_id: int, hours: int = 1):
        """Count access attempts by card in recent hours"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return session.query(cls).filter(
            cls.card_id == card_id,
            cls.timestamp >= since
        ).count()
    
    # Instance Methods
    
    def record_exit(self):
        """Record exit time and calculate duration"""
        if self.is_entry and not self.exit_time:
            self.exit_time = datetime.utcnow()
            delta = self.exit_time - self.timestamp
            self.duration_seconds = int(delta.total_seconds())
    
    def mark_suspicious(self, reason: str = None):
        """Flag this log as suspicious"""
        self.is_suspicious = True
        if reason:
            self.notes = f"Suspicious: {reason}"
    
    def trigger_alert(self, alert_type: str = None):
        """Trigger security alert for this log"""
        self.alert_triggered = True
        if alert_type:
            current_notes = self.notes or ""
            self.notes = f"{current_notes}\nAlert: {alert_type}".strip()
    
    def add_note(self, note: str):
        """Add note to existing notes"""
        if self.notes:
            self.notes = f"{self.notes}\n{note}"
        else:
            self.notes = note
    
    def to_dict(self, include_details: bool = False) -> dict:
        """Convert log to dictionary"""
        data = {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'status': self.status.value,
            'user_id': self.user_id,
            'card_id': self.card_id,
            'zone_id': self.zone_id,
            'device_id': self.device_id,
            'reason': self.reason,
            'is_entry': self.is_entry,
            'is_success': self.is_success
        }
        
        if include_details:
            data.update({
                'uid_attempted': self.uid_attempted,
                'exit_time': self.exit_time.isoformat() if self.exit_time else None,
                'time_in_zone': self.time_in_zone,
                'duration_seconds': self.duration_seconds,
                'is_suspicious': self.is_suspicious,
                'alert_triggered': self.alert_triggered,
                'decision_time_ms': self.decision_time_ms,
                'device_location': self.device_location,
                'ip_address': self.ip_address,
                'notes': self.notes
            })
        
        return data
