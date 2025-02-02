from appname.src.config.config import Config
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
import json
import inspect

Base = declarative_base()

class Model(Base):
    __abstract__ = True
    
    __required_fields = {}
    __field_types = {}

    @classmethod
    def initialize_from_sqlalchemy(cls, sqlalchemy_model):
        cls.__required_fields = {
            column.name: column.nullable for column in sqlalchemy_model.__table__.columns
        }
        cls.__field_types = {
            column.name: column.type.python_type for column in sqlalchemy_model.__table__.columns
        }
    
    def validate(self):
        for field in self.__required_fields:
            if field not in self.__dict__ or self.__dict__[field] is None:
                return False
        for field, field_type in self.__field_types.items():
            if field in self.__dict__ and not isinstance(self.__dict__[field], field_type):
                return False
        return True
    
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    def json(self):
        return json.dumps(self.to_dict(), indent=4)
    
    @classmethod
    def list_to_json(cls, objects):
        return json.dumps([obj.to_dict() for obj in objects], indent=4)

    @classmethod
    def _get_session(cls) -> Session:
        return Config.get_db_session()

    def save(self):
        session = Model._get_session() 
        try:
            session.add(self)
            session.commit()
            session.refresh(self)
        except Exception:
            session.rollback()
        finally:
            session.close()

    @classmethod
    def get(cls, **filters):
        if not cls._is_allowed():
            print(cls.__name__)
            raise PermissionError(f"Access denied: Only {cls.__name__}Controller can call this method.")
        
        session = cls._get_session()
        try:
            query = session.query(cls)
            for key, value in filters.items():
                if isinstance(value, list):
                    query = query.filter(getattr(cls, key).in_(value))
                else:
                    query = query.filter(getattr(cls, key) == value)
            return query.first()
        except Exception:
            return None
        finally:
            session.close()

    @classmethod
    def get_all(cls, **filters):
        if not cls._is_allowed():
            raise PermissionError(f"Access denied: Only {cls.__class__.__name__}Controller can call this method.")
        
        session = cls._get_session()
        try:
            query = session.query(cls)
            for key, value in filters.items():
                if isinstance(value, list):
                    query = query.filter(getattr(cls, key).in_(value))
                else:
                    query = query.filter(getattr(cls, key) == value)
            return query.all()
        except Exception:
            return []
        finally:
            session.close()

    def delete(self):
        session = Model._get_session()
        try:
            session.delete(self)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    @classmethod
    def delete_all(cls, **filters):
        if not cls._is_allowed():
            raise PermissionError(f"Access denied: Only {cls.__class__.__name__}Controller can call this method.")
        
        session = cls._get_session()
        try:
            query = session.query(cls)
            for key, value in filters.items():
                if isinstance(value, list):
                    query = query.filter(getattr(cls, key).in_(value))
                else:
                    query = query.filter(getattr(cls, key) == value)
            deleted_count = query.delete(synchronize_session=False)
            session.commit()
            return deleted_count
        except Exception:
            session.rollback()
            return 0
        finally:
            session.close()

