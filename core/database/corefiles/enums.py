from enum import Enum
from typing import List


# Access Status 

class AccessStatus(str, Enum):
   
    GRANTED = "granted"             
    DENIED = "denied"                
    EXPIRED = "expired"            
    BLACKLISTED = "blacklisted"     
    INACTIVE = "inactive"            
    INVALID_TIME = "invalid_time"    
    INVALID_ZONE = "invalid_zone"  
    INVALID_CARD = "invalid_card"    
    
    @classmethod
    def success_statuses(cls) -> List['AccessStatus']:
       
        return [cls.GRANTED]
    
    @classmethod
    def failure_statuses(cls) -> List['AccessStatus']:
      
        return [
            cls.DENIED, cls.EXPIRED, cls.BLACKLISTED,
            cls.INACTIVE, cls.INVALID_TIME, cls.INVALID_ZONE,
            cls.INVALID_CARD
        ]
    
    def is_success(self) -> bool:
      
        return self == self.GRANTED
    
    def get_persian_name(self) -> str:
        
        persian_names = {
            self.GRANTED: "دسترسی مجاز",
            self.DENIED: "دسترسی رد شده",
            self.EXPIRED: "کارت منقضی",
            self.BLACKLISTED: "لیست سیاه",
            self.INACTIVE: "غیرفعال",
            self.INVALID_TIME: "زمان نامعتبر",
            self.INVALID_ZONE: "زون نامعتبر",
            self.INVALID_CARD: "کارت نامعتبر"
        }
        return persian_names.get(self, self.value)



# Card Status 


class CardStatus(str, Enum):
   
    ACTIVE = "active"          
    INACTIVE = "inactive"      
    SUSPENDED = "suspended"    
    EXPIRED = "expired"       
    LOST = "lost"              
    STOLEN = "stolen"          
    DAMAGED = "damaged"        
    PENDING = "pending"       
    
    @classmethod
    def active_statuses(cls) -> List['CardStatus']:
      
        return [cls.ACTIVE]
    
    @classmethod
    def blocked_statuses(cls) -> List['CardStatus']:
      
        return [cls.LOST, cls.STOLEN, cls.SUSPENDED]
    
    def is_usable(self) -> bool:
      
        return self == self.ACTIVE
    
    def get_persian_name(self) -> str:
       
        persian_names = {
            self.ACTIVE: "فعال",
            self.INACTIVE: "غیرفعال",
            self.SUSPENDED: "معلق",
            self.EXPIRED: "منقضی",
            self.LOST: "گم شده",
            self.STOLEN: "سرقت شده",
            self.DAMAGED: "آسیب دیده",
            self.PENDING: "در انتظار"
        }
        return persian_names.get(self, self.value)



# User Role 


class UserRole(str, Enum):
    
    SUPER_ADMIN = "super_admin"  
    ADMIN = "admin"             
    MANAGER = "manager"         
    EMPLOYEE = "employee"       
    VISITOR = "visitor"          
    CONTRACTOR = "contractor"   
    SECURITY = "security"      
    GUEST = "guest"              
    
    @classmethod
    def admin_roles(cls) -> List['UserRole']:
       
        return [cls.SUPER_ADMIN, cls.ADMIN]
    
    @classmethod
    def staff_roles(cls) -> List['UserRole']:
        
        return [cls.MANAGER, cls.EMPLOYEE, cls.SECURITY]
    
    @classmethod
    def temporary_roles(cls) -> List['UserRole']:
        
        return [cls.VISITOR, cls.CONTRACTOR, cls.GUEST]
    
    def get_priority_level(self) -> int:
        
        priority_map = {
            self.SUPER_ADMIN: 100,
            self.ADMIN: 90,
            self.MANAGER: 70,
            self.SECURITY: 60,
            self.EMPLOYEE: 50,
            self.CONTRACTOR: 30,
            self.VISITOR: 20,
            self.GUEST: 10
        }
        return priority_map.get(self, 0)
    
    def is_admin(self) -> bool:
       
        return self in self.admin_roles()
    
    def get_persian_name(self) -> str:
        persian_names = {
            self.SUPER_ADMIN: "مدیر ارشد",
            self.ADMIN: "مدیر سیستم",
            self.MANAGER: "مدیر",
            self.EMPLOYEE: "کارمند",
            self.VISITOR: "بازدیدکننده",
            self.CONTRACTOR: "پیمانکار",
            self.SECURITY: "نگهبان",
            self.GUEST: "مهمان"
        }
        return persian_names.get(self, self.value)


# Policy Type 

class PolicyType(str, Enum):
    
    WHITELIST = "whitelist"        
    BLACKLIST = "blacklist"        
    TIME_BASED = "time_based"     
    ROLE_BASED = "role_based"     
    ZONE_BASED = "zone_based"
    LEVEL_BASED = "level_based"   
    CUSTOM = "custom"              
    
    def get_persian_name(self) -> str:
      
        persian_names = {
            self.WHITELIST: "لیست سفید",
            self.BLACKLIST: "لیست سیاه",
            self.TIME_BASED: "زمان‌بندی شده",
            self.ROLE_BASED: "مبتنی بر نقش",
            self.ZONE_BASED: "مبتنی بر زون",
            self.LEVEL_BASED: "مبتنی بر سطح",
            self.CUSTOM: "سفارشی"
        }
        return persian_names.get(self, self.value)



# Device Type 


class DeviceType(str, Enum):
    
    READER_RFID = "reader_rfid"     
    READER_NFC = "reader_nfc"      
    MOBILE_APP = "mobile_app"       
    WEB_INTERFACE = "web_interface" 
    TURNSTILE = "turnstile"          
    GATE = "gate"                  
    DOOR_LOCK = "door_lock"       
    SIMULATED = "simulated"         

    def get_persian_name(self) -> str:
        """دریافت نام فارسی نوع دستگاه"""
        persian_names = {
            self.READER_RFID: "خواننده RFID",
            self.READER_NFC: "خواننده NFC",
            self.MOBILE_APP: "اپلیکیشن موبایل",
            self.WEB_INTERFACE: "رابط وب",
            self.TURNSTILE: "گردان",
            self.GATE: "گیت",
            self.DOOR_LOCK: "قفل درب",
            self.SIMULATED: "شبیه‌سازی"
        }
        return persian_names.get(self, self.value)



# Day of Week 

class DayOfWeek(int, Enum):
    MONDAY = 1      
    TUESDAY = 2     
    WEDNESDAY = 3   
    THURSDAY = 4   
    FRIDAY = 5      
    SATURDAY = 6    
    SUNDAY = 7      
    
    @classmethod
    def weekdays(cls) -> List['DayOfWeek']:
       
        return [cls.SATURDAY, cls.SUNDAY, cls.MONDAY, cls.TUESDAY, cls.WEDNESDAY]
    
    @classmethod
    def weekend(cls) -> List['DayOfWeek']:

        return [cls.THURSDAY, cls.FRIDAY]
    
    def get_persian_name(self) -> str:
        persian_names = {
            self.MONDAY: "دوشنبه",
            self.TUESDAY: "سه‌شنبه",
            self.WEDNESDAY: "چهارشنبه",
            self.THURSDAY: "پنج‌شنبه",
            self.FRIDAY: "جمعه",
            self.SATURDAY: "شنبه",
            self.SUNDAY: "یکشنبه"
        }
        return persian_names.get(self, str(self.value))



# Helper Functions 
def get_all_enum_values(enum_class) -> List[str]:
   
    return [item.value for item in enum_class]


def get_enum_choices(enum_class) -> List[tuple]:
    
    return [(item.value, item.value) for item in enum_class]

# Export All
__all__ = [
    'AccessStatus',
    'CardStatus',
    'UserRole',
    'PolicyType',
    'DeviceType',
    'DayOfWeek',
    'get_all_enum_values',
    'get_enum_choices',
]