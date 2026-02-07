from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, 
    ForeignKey, Enum as SQLEnum, Text, Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session as OrmSession
from sqlalchemy.sql import func
import hashlib
import secrets


Base = declarative_base()


# ============================================================================
# Enums - تعاریف نوع شمارشی
# ============================================================================

class AccessStatus(str, Enum):
    """وضعیت‌های دسترسی"""
    GRANTED = "granted"          # دسترسی داده شد
    DENIED = "denied"            # دسترسی رد شد
    EXPIRED = "expired"          # کارت منقضی شده
    BLACKLISTED = "blacklisted"  # در لیست سیاه
    INACTIVE = "inactive"        # غیرفعال
    INVALID_TIME = "invalid_time" # خارج از بازه زمانی مجاز


class CardStatus(str, Enum):
    """وضعیت‌های کارت"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    LOST = "lost"
    STOLEN = "stolen"


class UserRole(str, Enum):
    """نقش‌های کاربری"""
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    VISITOR = "visitor"
    CONTRACTOR = "contractor"


class PolicyType(str, Enum):
    """نوع سیاست دسترسی"""
    WHITELIST = "whitelist"  # فقط مجازها
    BLACKLIST = "blacklist"  # همه به‌جز ممنوعه‌ها
    TIME_BASED = "time_based"  # بر اساس زمان
    ROLE_BASED = "role_based"  # بر اساس نقش


# ============================================================================
# Association Tables - جداول رابطهMany-to-Many
# ============================================================================

user_zone_association = Table(
    'user_zone_association',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column('zone_id', Integer, ForeignKey('zones.id', ondelete='CASCADE'))
)


# ============================================================================
# Main Models - مدل‌های اصلی
# ============================================================================

class User(Base):
    """
    مدل کاربر
    شامل اطلاعات شخصی و نقش کاربران در سیستم
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # اطلاعات شخصی
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    
    # اطلاعات سازمانی
    employee_id = Column(String(50), unique=True, nullable=True, index=True)
    department = Column(String(100), nullable=True)
    position = Column(String(100), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.EMPLOYEE, nullable=False)
    
    # وضعیت
    is_active = Column(Boolean, default=True, nullable=False)
    
    # زمان‌ها
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_access = Column(DateTime, nullable=True)
    
    # روابط
    cards = relationship("Card", back_populates="user", cascade="all, delete-orphan")
    access_logs = relationship("AccessLog", back_populates="user", cascade="all, delete-orphan")
    zones = relationship("Zone", secondary=user_zone_association, back_populates="users")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.first_name} {self.last_name}', role={self.role})>"

    @property
    def full_name(self):
        """نام کامل کاربر"""
        return f"{self.first_name} {self.last_name}"

    def has_active_card(self) -> bool:
        """بررسی داشتن کارت فعال"""
        return any(card.status == CardStatus.ACTIVE for card in self.cards)


class Card(Base):
    """
    مدل کارت NFC
    شامل اطلاعات کارت‌های NFC و وضعیت آن‌ها
    """
    __tablename__ = 'cards'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # شناسه یکتای کارت (رمزنگاری شده)
    uid = Column(String(255), unique=True, nullable=False, index=True)
    uid_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA-256
    
    # اطلاعات کارت
    card_number = Column(String(50), unique=True, nullable=True)
    card_type = Column(String(50), default="RFID", nullable=False)
    
    # ارتباط با کاربر
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # وضعیت و اعتبار
    status = Column(SQLEnum(CardStatus), default=CardStatus.ACTIVE, nullable=False)
    issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    
    # یادداشت‌ها
    notes = Column(Text, nullable=True)
    
    # زمان‌ها
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    
    # روابط
    user = relationship("User", back_populates="cards")
    access_logs = relationship("AccessLog", back_populates="card", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Card(id={self.id}, uid_hash={self.uid_hash[:8]}..., status={self.status})>"

    @staticmethod
    def hash_uid(uid: str) -> str:
        """رمزنگاری UID با SHA-256"""
        return hashlib.sha256(uid.encode()).hexdigest()

    def is_valid(self) -> bool:
        """بررسی اعتبار کارت"""
        if self.status != CardStatus.ACTIVE:
            return False
        
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        
        return True

    def check_access(self, zone: 'Zone' = None) -> tuple[bool, str]:
        """
        بررسی دسترسی کارت
        
        Returns:
            tuple: (دسترسی_مجاز, دلیل)
        """
        if not self.is_valid():
            if self.status != CardStatus.ACTIVE:
                return False, f"کارت {self.status.value} است"
            elif self.expires_at and self.expires_at < datetime.utcnow():
                return False, "کارت منقضی شده"
        
        if not self.user.is_active:
            return False, "کاربر غیرفعال است"
        
        if zone and zone not in self.user.zones:
            return False, f"دسترسی به زون {zone.name} وجود ندارد"
        
        return True, "دسترسی مجاز"


class Zone(Base):
    """
    مدل زون (محدوده دسترسی)
    تعریف مناطق و محدوده‌های مختلف با سطوح دسترسی متفاوت
    """
    __tablename__ = 'zones'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # اطلاعات زون
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    code = Column(String(20), unique=True, nullable=True)  # کد اختصاری
    
    # سطح امنیتی (1=پایین، 5=بالا)
    security_level = Column(Integer, default=1, nullable=False)
    
    # موقعیت فیزیکی
    building = Column(String(100), nullable=True)
    floor = Column(String(20), nullable=True)
    location = Column(String(255), nullable=True)
    
    # وضعیت
    is_active = Column(Boolean, default=True, nullable=False)
    
    # زمان‌ها
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # روابط
    users = relationship("User", secondary=user_zone_association, back_populates="zones")
    access_logs = relationship("AccessLog", back_populates="zone", cascade="all, delete-orphan")
    policies = relationship("AccessPolicy", back_populates="zone", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Zone(id={self.id}, name='{self.name}', level={self.security_level})>"


class AccessLog(Base):
    """
    مدل لاگ دسترسی
    ثبت تمامی تلاش‌های دسترسی (موفق و ناموفق)
    """
    __tablename__ = 'access_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # ارتباطات
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    card_id = Column(Integer, ForeignKey('cards.id', ondelete='SET NULL'), nullable=True)
    zone_id = Column(Integer, ForeignKey('zones.id', ondelete='SET NULL'), nullable=True)
    
    # اطلاعات دسترسی
    uid_attempted = Column(String(255), nullable=False)  # UID تلاش شده (حتی اگر نامعتبر باشد)
    status = Column(SQLEnum(AccessStatus), nullable=False)
    
    # جزئیات
    reason = Column(String(255), nullable=True)  # دلیل رد یا قبول
    device_id = Column(String(100), nullable=True)  # شناسه دستگاه خواننده
    ip_address = Column(String(45), nullable=True)  # IP دستگاه
    
    # زمان
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # اطلاعات اضافی (JSON)
    metadata = Column(Text, nullable=True)
    
    # روابط
    user = relationship("User", back_populates="access_logs")
    card = relationship("Card", back_populates="access_logs")
    zone = relationship("Zone", back_populates="access_logs")

    def __repr__(self):
        return f"<AccessLog(id={self.id}, status={self.status}, time={self.timestamp})>"

    @classmethod
    def create_log(cls, session: OrmSession, uid: str, status: AccessStatus, 
                   user_id: int = None, card_id: int = None, zone_id: int = None,
                   reason: str = None, device_id: str = None):
        """
        ایجاد لاگ جدید
        """
        log = cls(
            uid_attempted=uid,
            status=status,
            user_id=user_id,
            card_id=card_id,
            zone_id=zone_id,
            reason=reason,
            device_id=device_id,
            timestamp=datetime.utcnow()
        )
        session.add(log)
        return log


class AccessPolicy(Base):
    """
    مدل سیاست دسترسی
    تعریف قوانین و محدودیت‌های دسترسی برای زون‌ها
    """
    __tablename__ = 'access_policies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # ارتباط با زون
    zone_id = Column(Integer, ForeignKey('zones.id', ondelete='CASCADE'), nullable=False)
    
    # نوع سیاست
    policy_type = Column(SQLEnum(PolicyType), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # قوانین زمانی
    time_start = Column(String(5), nullable=True)  # مثال: "08:00"
    time_end = Column(String(5), nullable=True)    # مثال: "18:00"
    days_of_week = Column(String(50), nullable=True)  # مثال: "1,2,3,4,5" (دوشنبه تا جمعه)
    
    # محدودیت‌های نقش
    allowed_roles = Column(String(255), nullable=True)  # مثال: "admin,manager"
    
    # وضعیت
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=0, nullable=False)  # اولویت اعمال
    
    # زمان‌ها
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # روابط
    zone = relationship("Zone", back_populates="policies")

    def __repr__(self):
        return f"<AccessPolicy(id={self.id}, type={self.policy_type}, zone={self.zone_id})>"

    def is_time_allowed(self, check_time: datetime = None) -> bool:
        """بررسی بازه زمانی مجاز (با لحاظ کردن اختلاف زمانی)"""
        if not check_time:
            check_time = datetime.utcnow()
        
        # فرض کنیم میخواهیم UTC را به وقت ایران تبدیل کنیم (یا هر تایم زون تنظیم شده در کانفیگ)
        # روش ساده: اضافه کردن دستی آفست (برای پروژه های کوچک)
        # روش حرفه ای: استفاده از pytz (که نیاز به نصب دارد)
        
        # اینجا فرض میکنیم check_time ورودی، قبلاً به وقت محلی تبدیل شده است
        # یا اینکه همینجا تبدیلش میکنیم (مثلاً +3.5 ساعت)
        local_time = check_time + timedelta(hours=3, minutes=30) 

        # بررسی روز هفته
        if self.days_of_week:
            allowed_days = [int(d) for d in self.days_of_week.split(',')]
            # isoweekday: Mon=1, Sun=7
            if local_time.isoweekday() not in allowed_days:
                return False
        
        # بررسی ساعت
        if self.time_start and self.time_end:
            current_str = local_time.strftime("%H:%M")
            if not (self.time_start <= current_str <= self.time_end):
                return False
        
        return True

# ============================================================================
# Helper Functions - توابع کمکی
# ============================================================================

def init_db(engine):
    """ایجاد تمامی جداول در دیتابیس"""
    Base.metadata.create_all(engine)
    print("✅ تمامی جداول با موفقیت ایجاد شدند")


def drop_all_tables(engine):
    """حذف تمامی جداول (استفاده با احتیاط!)"""
    Base.metadata.drop_all(engine)
    print("⚠️ تمامی جداول حذف شدند")


# ============================================================================
# Example Usage - نمونه استفاده
# ============================================================================

if __name__ == "__main__":
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # ایجاد موتور دیتابیس
    engine = create_engine('sqlite:///nfc_access_control.db', echo=True)
    
    # ایجاد جداول
    init_db(engine)
    
    # ایجاد Session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # مثال: ایجاد یک کاربر
    user = User(
        first_name="علی",
        last_name="احمدی",
        email="ali.ahmadi@example.com",
        employee_id="EMP001",
        department="IT",
        role=UserRole.EMPLOYEE
    )
    session.add(user)
    session.commit()
    
    # مثال: ایجاد یک کارت برای کاربر
    uid = "04:52:D6:AA:12:34:80"
    card = Card(
        uid=uid,
        uid_hash=Card.hash_uid(uid),
        user_id=user.id,
        status=CardStatus.ACTIVE,
        expires_at=datetime.utcnow() + timedelta(days=365)
    )
    session.add(card)
    session.commit()
    
    # مثال: ایجاد یک زون
    zone = Zone(
        name="IT Department",
        description="بخش فناوری اطلاعات",
        security_level=3,
        building="ساختمان اصلی",
        floor="طبقه 2"
    )
    session.add(zone)
    session.commit()
    
    # اضافه کردن کاربر به زون
    user.zones.append(zone)
    session.commit()
    
    # مثال: ثبت لاگ دسترسی
    log = AccessLog.create_log(
        session=session,
        uid=uid,
        status=AccessStatus.GRANTED,
        user_id=user.id,
        card_id=card.id,
        zone_id=zone.id,
        reason="دسترسی موفق",
        device_id="READER_001"
    )
    session.commit()
    
    print(f"\n✅ داده‌های نمونه با موفقیت ایجاد شدند!")
    print(f"👤 کاربر: {user.full_name}")
    print(f"💳 کارت: {card.uid}")
    print(f"🏢 زون: {zone.name}")
    print(f"📝 لاگ: {log.status.value}")
    
    session.close()