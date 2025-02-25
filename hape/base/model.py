from hape.config import Config
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
import json

Base = declarative_base()

class Model(Base):
    __abstract__ = True
    
    __required_fields = {}
    __field_types = {}

    @classmethod
    def initialize_from_sqlalchemy(cls, sqlalchemy_base_model):
        cls.__required_fields = {
            column.name: not column.nullable for column in sqlalchemy_base_model.__table__.columns
        }
        cls.__field_types = {
            column.name: column.type.python_type for column in sqlalchemy_base_model.__table__.columns
        }
    
    def validate(self):
        for field, is_required in self.__required_fields.items():
            if is_required and field not in self.__dict__ or self.__dict__[field] is None:
                if field not in ['id', 'created_at']:
                    return False
        for field, field_type in self.__field_types.items():
            if field in self.__dict__ and not isinstance(self.__dict__[field], field_type):
                print("invalid!")
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
        exit_status = True
        try:
            session.add(self)
            session.commit()
            session.refresh(self)
        except Exception:
            exit_status = False
            session.rollback()
            print("---rollback---")
        finally:
            session.close()
            print("---close---")
            return exit_status

    @classmethod
    def get(cls, **filters):
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
