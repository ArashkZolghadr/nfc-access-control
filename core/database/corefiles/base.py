from datetime import datetime
from sqlalchemy import Column , Integer  , DateTime
from sqlalchemy.ext.declarative import declarative_base , declared_attr
from sqlalchemy import MetaData


# Naming Convention
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=naming_convention)
Base = declarative_base(metadata=metadata)


# Mixins
class TimestampMixin:
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class PrimaryKeyMixin:

    id = Column(Integer, primary_key=True, autoincrement=True)

class BaseModel(Base, PrimaryKeyMixin, TimestampMixin):
    
    __abstract__ = True  

class SoftDeleteMixin: 
    deleted_at = Column(DateTime, nullable=True, default=None)
    
    def soft_delete(self):    
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        self.deleted_at = None
    
    def is_deleted(self) -> bool:
        return self.deleted_at is not None