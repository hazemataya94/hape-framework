from hape.hape_config import HapeConfig
from hape.logging import Logging
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
import json

Base = declarative_base()

class Model(Base):
    __abstract__ = True
    
    __required_fields = {}
    __field_types = {}

    logger = Logging.get_logger('hape.base.model')

    def __init__(self, **kwargs):
        self.logger = Logging.get_logger('hape.base.model')

    @classmethod
    def initialize_from_sqlalchemy(cls, sqlalchemy_base_model):
        cls.logger.debug(f"initialize_from_sqlalchemy({sqlalchemy_base_model})")
        cls.__required_fields = {
            column.name: not column.nullable for column in sqlalchemy_base_model.__table__.columns
        }
        cls.__field_types = {
            column.name: column.type.python_type for column in sqlalchemy_base_model.__table__.columns
        }
    
    def validate(self):
        self.logger.debug(f"validate()")
        for field, is_required in self.__required_fields.items():
            if is_required and field not in self.__dict__ or self.__dict__[field] is None:
                if field not in ['id', 'created_at']:
                    return False
        for field, field_type in self.__field_types.items():
            if field in self.__dict__ and not isinstance(self.__dict__[field], field_type):
                print("invalid!")
                return False
        return True
    
    def dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    def json(self, pretty=True):
        return json.dumps(self.dict(), indent=4) if pretty else json.dumps(self.dict())
    
    @classmethod
    def list_to_json(cls, objects, pretty=True):
        return json.dumps([obj.dict() for obj in objects], indent=4) if pretty else json.dumps([obj.dict() for obj in objects])

    @classmethod
    def _get_session(cls) -> Session:
        return HapeConfig.get_db_session()

    def save(self):
        self.logger.debug(f"save({self.json(pretty=False)})")
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
        cls.logger.debug(f"get({filters})")
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
        cls.logger.debug(f"get_all({filters})")
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
        self.logger.debug(f"delete()")
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
        cls.logger.debug(f"delete_all({filters})")
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
