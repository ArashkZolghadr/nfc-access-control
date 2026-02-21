"""
AccessPolicy Model
==================
Defines access control policies and rules
"""
from datetime import datetime, timedelta
from typing import List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from core.database.corefiles.base import Base
from core.database.corefiles.enums import PolicyType, UserRole, DayOfWeek


class AccessPolicy(Base):
    """
    Access policy model
    Defines rules and restrictions for zone access
    """
    __tablename__ = 'access_policies'

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Zone Association
    zone_id = Column(Integer, ForeignKey('zones.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Policy Identification
    policy_type = Column(SQLEnum(PolicyType), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(50), unique=True, nullable=True)
    description = Column(Text, nullable=True)
    
    # Time-Based Rules
    time_start = Column(String(5), nullable=True)
    time_end = Column(String(5), nullable=True)
    days_of_week = Column(String(50), nullable=True)
    
    # Date-Based Rules
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    
    # Role-Based Rules
    allowed_roles = Column(String(255), nullable=True)
    denied_roles = Column(String(255), nullable=True)
    
    # Whitelist/Blacklist
    whitelist_users = Column(Text, nullable=True)
    blacklist_users = Column(Text, nullable=True)
    
    # Capacity Limits
    max_concurrent_users = Column(Integer, nullable=True)
    max_daily_entries = Column(Integer, nullable=True)
    
    # Duration Limits
    max_duration_minutes = Column(Integer, nullable=True)
    cooldown_minutes = Column(Integer, nullable=True)
    
    # Security Requirements
    require_escort = Column(Boolean, default=False, nullable=False)
    require_approval = Column(Boolean, default=False, nullable=False)
    require_two_factor = Column(Boolean, default=False, nullable=False)
    
    # Status and Priority
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    priority = Column(Integer, default=0, nullable=False, index=True)
    
    # Override Settings
    allow_emergency_override = Column(Boolean, default=True, nullable=False)
    allow_admin_override = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_applied = Column(DateTime, nullable=True)
    
    # Audit
    created_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    updated_by = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # Additional Info
    notes = Column(Text, nullable=True)
    enforcement_level = Column(String(20), default="strict", nullable=False)
    
    # Relationships
    zone = relationship("Zone", back_populates="policies")

    def __repr__(self):
        return f"<AccessPolicy(id={self.id}, name='{self.name}', type={self.policy_type.value})>"

    def __str__(self):
        return f"{self.name} ({self.policy_type.value})"

    # Properties
    
    @property
    def is_valid(self) -> bool:
        """Check if policy is currently valid"""
        now = datetime.utcnow()
        
        if self.valid_from and now < self.valid_from:
            return False
        
        if self.valid_until and now > self.valid_until:
            return False
        
        return True
    
    @property
    def is_time_restricted(self) -> bool:
        """Check if policy has time restrictions"""
        return bool(self.time_start and self.time_end)
    
    @property
    def is_role_restricted(self) -> bool:
        """Check if policy has role restrictions"""
        return bool(self.allowed_roles or self.denied_roles)
    
    # Validation Methods
    
    def is_time_allowed(self, check_time: datetime = None) -> bool:
        """
        Check if current time is within allowed period
        
        Args:
            check_time: Time to check (default: now)
            
        Returns:
            bool: True if time is allowed
        """
        if not check_time:
            check_time = datetime.utcnow()
        
        # Convert to local time (adjust offset as needed)
        local_time = check_time + timedelta(hours=3, minutes=30)
        
        # Check day of week
        if self.days_of_week:
            allowed_days = [int(d) for d in self.days_of_week.split(',')]
            if local_time.isoweekday() not in allowed_days:
                return False
        
        # Check time range
        if self.time_start and self.time_end:
            current_str = local_time.strftime("%H:%M")
            if not (self.time_start <= current_str <= self.time_end):
                return False
        
        return True
    
    def is_role_allowed(self, user_role: UserRole) -> bool:
        """
        Check if user role is allowed
        
        Args:
            user_role: UserRole enum
            
        Returns:
            bool: True if role is allowed
        """
        # Check denied roles first
        if self.denied_roles:
            denied = self.denied_roles.split(',')
            if user_role.value in denied:
                return False
        
        # Check allowed roles
        if self.allowed_roles:
            allowed = self.allowed_roles.split(',')
            return user_role.value in allowed
        
        # If no role restrictions, allow all
        return True
    
    def is_user_whitelisted(self, user_id: int) -> bool:
        """Check if user is in whitelist"""
        if not self.whitelist_users:
            return False
        user_ids = [int(uid) for uid in self.whitelist_users.split(',')]
        return user_id in user_ids
    
    def is_user_blacklisted(self, user_id: int) -> bool:
        """Check if user is in blacklist"""
        if not self.blacklist_users:
            return False
        user_ids = [int(uid) for uid in self.blacklist_users.split(',')]
        return user_id in user_ids
    
    def check_access(self, user=None, check_time: datetime = None) -> tuple[bool, str]:
        """
        Comprehensive access check
        
        Args:
            user: User object
            check_time: Time to check
            
        Returns:
            tuple: (access_allowed, reason)
        """
        # Check if policy is active
        if not self.is_active:
            return True, "Policy inactive"  # Inactive policies allow access
        
        # Check validity period
        if not self.is_valid:
            return True, "Policy not valid yet"
        
        # Check time restrictions
        if self.is_time_restricted:
            if not self.is_time_allowed(check_time):
                return False, "Outside allowed time"
        
        # User-specific checks
        if user:
            # Check blacklist
            if self.is_user_blacklisted(user.id):
                return False, "User is blacklisted"
            
            # For whitelist policies, must be whitelisted
            if self.policy_type == PolicyType.WHITELIST:
                if not self.is_user_whitelisted(user.id):
                    return False, "User not in whitelist"
            
            # Check role restrictions
            if self.is_role_restricted:
                if not self.is_role_allowed(user.role):
                    return False, f"Role '{user.role.value}' not allowed"
        
        return True, "Policy check passed"
    
    # Management Methods
    
    def activate(self):
        """Activate the policy"""
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def deactivate(self):
        """Deactivate the policy"""
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def add_to_whitelist(self, user_ids: List[int]):
        """Add users to whitelist"""
        existing = set(self.whitelist_users.split(',')) if self.whitelist_users else set()
        existing.update([str(uid) for uid in user_ids])
        self.whitelist_users = ','.join(sorted(existing))
        self.updated_at = datetime.utcnow()
    
    def remove_from_whitelist(self, user_ids: List[int]):
        """Remove users from whitelist"""
        if not self.whitelist_users:
            return
        existing = set(self.whitelist_users.split(','))
        existing.difference_update([str(uid) for uid in user_ids])
        self.whitelist_users = ','.join(sorted(existing)) if existing else None
        self.updated_at = datetime.utcnow()
    
    def add_to_blacklist(self, user_ids: List[int]):
        """Add users to blacklist"""
        existing = set(self.blacklist_users.split(',')) if self.blacklist_users else set()
        existing.update([str(uid) for uid in user_ids])
        self.blacklist_users = ','.join(sorted(existing))
        self.updated_at = datetime.utcnow()
    
    def remove_from_blacklist(self, user_ids: List[int]):
        """Remove users from blacklist"""
        if not self.blacklist_users:
            return
        existing = set(self.blacklist_users.split(','))
        existing.difference_update([str(uid) for uid in user_ids])
        self.blacklist_users = ','.join(sorted(existing)) if existing else None
        self.updated_at = datetime.utcnow()
    
    def set_time_restriction(self, start: str, end: str, days: List[int] = None):
        """
        Set time-based restrictions
        
        Args:
            start: Start time in HH:MM format
            end: End time in HH:MM format
            days: List of day numbers (1=Monday, 7=Sunday)
        """
        self.time_start = start
        self.time_end = end
        if days:
            self.days_of_week = ','.join([str(d) for d in days])
        self.updated_at = datetime.utcnow()
    
    def set_role_restriction(self, allowed: List[str] = None, denied: List[str] = None):
        """
        Set role-based restrictions
        
        Args:
            allowed: List of allowed role values
            denied: List of denied role values
        """
        if allowed:
            self.allowed_roles = ','.join(allowed)
        if denied:
            self.denied_roles = ','.join(denied)
        self.updated_at = datetime.utcnow()
    
    def record_application(self):
        """Record that this policy was applied"""
        self.last_applied = datetime.utcnow()
    
    def to_dict(self, include_details: bool = False) -> dict:
        """Convert policy to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'policy_type': self.policy_type.value,
            'zone_id': self.zone_id,
            'is_active': self.is_active,
            'priority': self.priority,
            'is_valid': self.is_valid
        }
        
        if include_details:
            data.update({
                'description': self.description,
                'time_start': self.time_start,
                'time_end': self.time_end,
                'days_of_week': self.days_of_week,
                'allowed_roles': self.allowed_roles,
                'denied_roles': self.denied_roles,
                'require_escort': self.require_escort,
                'require_approval': self.require_approval,
                'require_two_factor': self.require_two_factor,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'last_applied': self.last_applied.isoformat() if self.last_applied else None
            })
        
        return data
