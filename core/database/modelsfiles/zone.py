"""
Zone Model
==========
Manages physical zones and access control areas
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.orm import relationship

from core.database.corefiles.base import Base
from core.database.corefiles.associations import user_zone_association


class Zone(Base):
    """
    Zone model for physical access control areas
    Defines locations with different security levels
    """
    __tablename__ = 'zones'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Zone Information
    name = Column(String(100), unique=True, nullable=False, index=True)
    code = Column(String(20), unique=True, nullable=True, index=True)
    description = Column(Text, nullable=True)
    zone_type = Column(String(50), default="office", nullable=False)
    
    # Security Level (1=lowest, 10=highest)
    security_level = Column(Integer, default=1, nullable=False, index=True)
    requires_escort = Column(Boolean, default=False, nullable=False)
    requires_two_factor = Column(Boolean, default=False, nullable=False)
    
    # Physical Location
    building = Column(String(100), nullable=True)
    floor = Column(String(20), nullable=True)
    room_number = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    
    # Geographic Coordinates (optional)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Capacity Management
    max_capacity = Column(Integer, nullable=True)
    current_occupancy = Column(Integer, default=0, nullable=False)
    
    # Status and Timing
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_restricted = Column(Boolean, default=False, nullable=False)
    restriction_reason = Column(Text, nullable=True)
    
    # Operating Hours (format: "HH:MM")
    open_time = Column(String(5), nullable=True)
    close_time = Column(String(5), nullable=True)
    
    # Emergency Settings
    emergency_exit = Column(Boolean, default=False, nullable=False)
    evacuation_priority = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_accessed = Column(DateTime, nullable=True)
    
    # Parent Zone (for hierarchical zones)
    parent_zone_id = Column(Integer, nullable=True, index=True)
    
    # Additional Info
    contact_person = Column(String(100), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    users = relationship(
        "User",
        secondary=user_zone_association,
        primaryjoin="Zone.id==user_zone_association.c.zone_id",
        secondaryjoin="User.id==user_zone_association.c.user_id",
        foreign_keys="[user_zone_association.c.zone_id, user_zone_association.c.user_id]",
        back_populates="zones",
        lazy='dynamic',
    )
    access_logs = relationship("AccessLog", back_populates="zone", cascade="all, delete-orphan", lazy='dynamic')
    policies = relationship("AccessPolicy", back_populates="zone", cascade="all, delete-orphan", lazy='dynamic')

    def __repr__(self):
        return f"<Zone(id={self.id}, name='{self.name}', level={self.security_level})>"

    def __str__(self):
        return f"{self.name} (Level {self.security_level})"

    # Properties
    
    @property
    def full_location(self) -> str:
        """Get complete location string"""
        parts = []
        if self.building:
            parts.append(self.building)
        if self.floor:
            parts.append(f"Floor {self.floor}")
        if self.room_number:
            parts.append(f"Room {self.room_number}")
        return ", ".join(parts) if parts else self.location or "Unknown"
    
    @property
    def is_at_capacity(self) -> bool:
        """Check if zone is at maximum capacity"""
        if not self.max_capacity:
            return False
        return self.current_occupancy >= self.max_capacity
    
    @property
    def occupancy_percentage(self) -> float:
        """Get occupancy as percentage"""
        if not self.max_capacity or self.max_capacity == 0:
            return 0.0
        return (self.current_occupancy / self.max_capacity) * 100
    
    @property
    def is_high_security(self) -> bool:
        """Check if this is a high security zone"""
        return self.security_level >= 7
    
    @property
    def available_capacity(self) -> int:
        """Get remaining capacity"""
        if not self.max_capacity:
            return 999999
        return max(0, self.max_capacity - self.current_occupancy)
    
    # Methods
    
    def is_open(self, check_time: datetime = None) -> bool:
        """Check if zone is currently open"""
        if not self.open_time or not self.close_time:
            return True
        
        if not check_time:
            check_time = datetime.utcnow()
        
        current_time = check_time.strftime("%H:%M")
        return self.open_time <= current_time <= self.close_time
    
    def can_enter(self, user=None) -> tuple[bool, str]:
        """
        Check if zone can be entered
        
        Args:
            user: User object (optional)
            
        Returns:
            tuple: (can_enter, reason)
        """
        # Check if zone is active
        if not self.is_active:
            return False, "Zone is inactive"
        
        # Check if restricted
        if self.is_restricted:
            return False, f"Zone is restricted: {self.restriction_reason}"
        
        # Check capacity
        if self.is_at_capacity:
            return False, "Zone is at maximum capacity"
        
        # Check operating hours
        if not self.is_open():
            return False, "Zone is closed"
        
        # Check user access if provided
        if user:
            if not self.has_user_access(user.id):
                return False, "User does not have access to this zone"
        
        return True, "Entry allowed"
    
    def has_user_access(self, user_id: int) -> bool:
        """Check if user has access to this zone"""
        return self.users.filter_by(id=user_id).count() > 0
    
    def get_authorized_users(self):
        """Get all users with access to this zone"""
        return self.users.all()
    
    def increment_occupancy(self):
        """Increase current occupancy count"""
        if not self.max_capacity or self.current_occupancy < self.max_capacity:
            self.current_occupancy += 1
            self.last_accessed = datetime.utcnow()
    
    def decrement_occupancy(self):
        """Decrease current occupancy count"""
        if self.current_occupancy > 0:
            self.current_occupancy -= 1
    
    def reset_occupancy(self):
        """Reset occupancy to zero"""
        self.current_occupancy = 0
    
    def activate(self):
        """Activate the zone"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self, reason: str = None):
        """Deactivate the zone"""
        self.is_active = False
        if reason:
            self.notes = f"Deactivated: {reason}"
        self.updated_at = datetime.utcnow()
    
    def restrict(self, reason: str):
        """Place zone under restriction"""
        self.is_restricted = True
        self.restriction_reason = reason
        self.updated_at = datetime.utcnow()
    
    def lift_restriction(self):
        """Remove restriction from zone"""
        self.is_restricted = False
        self.restriction_reason = None
        self.updated_at = datetime.utcnow()
    
    def set_operating_hours(self, open_time: str, close_time: str):
        """
        Set zone operating hours
        
        Args:
            open_time: Opening time in HH:MM format
            close_time: Closing time in HH:MM format
        """
        self.open_time = open_time
        self.close_time = close_time
        self.updated_at = datetime.utcnow()
    
    def get_access_history(self, limit: int = 10):
        """Get recent access logs for this zone"""
        return self.access_logs.order_by('timestamp desc').limit(limit).all()
    
    def get_active_policies(self):
        """Get all active policies for this zone"""
        return self.policies.filter_by(is_active=True).order_by('priority desc').all()
    
    def to_dict(self, include_stats: bool = False) -> dict:
        """Convert zone to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'zone_type': self.zone_type,
            'security_level': self.security_level,
            'full_location': self.full_location,
            'is_active': self.is_active,
            'is_restricted': self.is_restricted,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_stats:
            data.update({
                'current_occupancy': self.current_occupancy,
                'max_capacity': self.max_capacity,
                'occupancy_percentage': self.occupancy_percentage,
                'available_capacity': self.available_capacity,
                'is_at_capacity': self.is_at_capacity,
                'authorized_users_count': self.users.count(),
                'is_open': self.is_open()
            })
        
        return data
