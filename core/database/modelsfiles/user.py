"""
User Model
==========
Manages user accounts, roles, and personal information
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from core.database.corefiles.base import Base
from core.database.corefiles.enums import UserRole, CardStatus
from core.database.corefiles.associations import user_zone_association


class User(Base):
    """
    User model for access control system
    Stores personal info, organizational details, and manages relationships
    """
    __tablename__ = 'users'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    national_id = Column(String(50), unique=True, nullable=True, index=True)
    
    # Organizational Information
    employee_id = Column(String(50), unique=True, nullable=True, index=True)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.EMPLOYEE, nullable=False, index=True)
    manager_id = Column(Integer, nullable=True)
    
    # Authentication (for future web interface)
    password_hash = Column(String(255), nullable=True)
    last_login = Column(DateTime, nullable=True)
    login_attempts = Column(Integer, default=0, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    suspension_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_access = Column(DateTime, nullable=True, index=True)
    
    # Employment dates
    hire_date = Column(DateTime, nullable=True)
    termination_date = Column(DateTime, nullable=True)
    
    # Additional info
    profile_photo = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    cards = relationship("Card", back_populates="user", cascade="all, delete-orphan", lazy='dynamic')
    access_logs = relationship("AccessLog", back_populates="user", cascade="all, delete-orphan", lazy='dynamic')
    zones = relationship(
        "Zone",
        secondary=user_zone_association,
        primaryjoin="User.id==user_zone_association.c.user_id",
        secondaryjoin="Zone.id==user_zone_association.c.zone_id",
        foreign_keys="[user_zone_association.c.user_id, user_zone_association.c.zone_id]",
        back_populates="users",
        lazy='dynamic',
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role={self.role.value})>"

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    # Properties
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_name(self) -> str:
        """Get display name with employee ID if available"""
        if self.employee_id:
            return f"{self.full_name} ({self.employee_id})"
        return self.full_name
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges"""
        return self.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]
    
    @property
    def is_employed(self) -> bool:
        """Check if user is currently employed"""
        if self.termination_date and self.termination_date < datetime.utcnow():
            return False
        return True
    
    # Methods
    
    def has_active_card(self) -> bool:
        """Check if user has at least one active card"""
        return self.cards.filter_by(status=CardStatus.ACTIVE).count() > 0
    
    def get_active_cards(self):
        """Get all active cards for this user"""
        return self.cards.filter_by(status=CardStatus.ACTIVE).all()
    
    def has_zone_access(self, zone_id: int) -> bool:
        """Check if user has access to specific zone"""
        return self.zones.filter_by(id=zone_id).count() > 0
    
    def get_zones_list(self) -> list:
        """Get list of all accessible zones"""
        return self.zones.all()
    
    def update_last_access(self):
        """Update last access timestamp"""
        self.last_access = datetime.utcnow()
    
    def suspend(self, reason: str = None):
        """Suspend user account"""
        self.is_active = False
        self.suspension_reason = reason
        self.updated_at = datetime.utcnow()
    
    def activate(self):
        """Activate user account"""
        self.is_active = True
        self.suspension_reason = None
        self.updated_at = datetime.utcnow()
    
    def terminate_employment(self):
        """Mark user as terminated"""
        self.termination_date = datetime.utcnow()
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def get_access_history(self, limit: int = 10):
        """Get recent access logs"""
        return self.access_logs.order_by('timestamp desc').limit(limit).all()
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'employee_id': self.employee_id,
            'department': self.department,
            'position': self.position,
            'role': self.role.value,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_access': self.last_access.isoformat() if self.last_access else None,
        }
        
        if include_sensitive:
            data.update({
                'national_id': self.national_id,
                'is_verified': self.is_verified,
                'suspension_reason': self.suspension_reason,
                'notes': self.notes
            })
        
        return data
