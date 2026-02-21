"""
Database Association Tables
Many-to-Many relationship tables for the NFC Access Control System
"""
from sqlalchemy import Table, Column, Integer, String, ForeignKey, DateTime, Boolean
from datetime import datetime
from .base import Base


# ============================================================================
# User-Zone Association
# Defines which users have access to which zones
# ============================================================================
user_zone_association = Table(
    'user_zone_association',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('zone_id', Integer, ForeignKey('zones.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('granted_at', DateTime, default=datetime.utcnow, nullable=False),
    Column('granted_by', Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
    Column('expires_at', DateTime, nullable=True),
    Column('is_active', Boolean, default=True, nullable=False),
    Column('notes', String(255), nullable=True)
)


# ============================================================================
# Card-Zone Association (Optional)
# Direct card access to specific zones (bypassing user)
# ============================================================================
card_zone_association = Table(
    'card_zone_association',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('card_id', Integer, ForeignKey('cards.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('zone_id', Integer, ForeignKey('zones.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('granted_at', DateTime, default=datetime.utcnow, nullable=False),
    Column('expires_at', DateTime, nullable=True),
    Column('priority', Integer, default=0, nullable=False)
)


# ============================================================================
# Zone-Policy Association
# Link zones with their access policies
# ============================================================================
zone_policy_association = Table(
    'zone_policy_association',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('zone_id', Integer, ForeignKey('zones.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('policy_id', Integer, ForeignKey('access_policies.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('is_active', Boolean, default=True, nullable=False),
    Column('created_at', DateTime, default=datetime.utcnow, nullable=False)
)


# ============================================================================
# User-Policy Association
# Specific policy overrides for individual users
# ============================================================================
user_policy_association = Table(
    'user_policy_association',
    Base.metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('policy_id', Integer, ForeignKey('access_policies.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('is_override', Boolean, default=False, nullable=False),
    Column('created_at', DateTime, default=datetime.utcnow, nullable=False)
)


# ============================================================================
# Export all associations
# ============================================================================
__all__ = [
    'user_zone_association',
    'card_zone_association',
    'zone_policy_association',
    'user_policy_association',
]