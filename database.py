import enum
import config
import logging
import config

import sqlalchemy
from sqlalchemy import Column, Integer, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref
from geoalchemy2 import Geometry
from sqlalchemy.sql import func
from sqlalchemy import Enum

from shapely.geometry import (
    LineString,
    MultiLineString,
    MultiPoint,
    Point,
    Polygon,
    shape,
)
from shapely.geometry.base import BaseGeometry
from sqlalchemy.sql.expression import func as sqlexpr

from sqlalchemy.exc import SQLAlchemyError

# select class1_fi,class2_fi from lipas where typeCode=?
# select most frequent class1_fi,class2_fi combo

Base = declarative_base()

class GeometryType(enum.Enum):
    point = 0
    route = 1
    area = 2
    
# DESIGN: https://gis.stackexchange.com/a/11506
# DESIGN: https://stackoverflow.com/a/4813817
class Lipas(Base):

    __tablename__ = 'lipas'

    sports_place_id = Column('sports_place_id', Integer, primary_key=True,comment="lipas id")
    lastModified = Column('last_modified',DateTime, unique=False, server_default=func.now(), nullable=False,comment="Automatically updated last modified date from lipas")

    typeCode = Column('type_code',Integer, unique=False, nullable=False,comment="lipas category")
    cityCode = Column('city_code',Integer, unique=False, nullable=True,comment="cityCode")
    
    name_fi = Column(String, unique=False, nullable=False,comment="name of place")
    www = Column(String, unique=False, nullable=True,comment="webpage")
    geom = Column(Geometry(srid=config.epsg), unique=False, nullable=False,comment="geometry, can be point or (m)linestring/route or possibly an area")
    geomType = Column('geom_type',Enum(GeometryType), unique=False, nullable=False,comment="geom column type (possibly redundant)")
    
    #class1_fi = Column(String, unique=False, nullable=True,comment="virma class1")
    #class2_fi = Column(String, unique=False, nullable=True,comment="virma class2")
    
    #muncipali = Column(String, unique=False, nullable=True,comment="virma style muncipality | lipas:postalOffice")
    #subregion = Column(String, unique=False, nullable=True,comment="virma style subgregion | lipas:neighborhood")

    email = Column(String, unique=False, nullable=True,comment="email")

    owner = Column(String, unique=False, nullable=True,comment="owner")
    telephone = Column(String, unique=False, nullable=True,comment="tel")
    #www_picture = Column(String, unique=False, nullable=True,comment="URL to image")
    length_m = Column(Integer, unique=False, nullable=True,comment="autocalculated length if route")
    
    annotation = relationship(
        "Annotations", uselist=False, backref="lipas")

    def __repr__(self):
        return f"<LipasMirrorDB (id={self.sports_place_id!r}, name={self.name_fi!r})>"

class LipasTypes(Base):

    __tablename__ = 'lipas_types'

    typeCode = Column('type_code',Integer, primary_key=True,comment="typeCode")
    typeName = Column('type_name',String, unique=False, nullable=False,comment="typeName")
    
    def __repr__(self):
        return f"<LipasType (id={self.typeCode!r}, name={self.typeName!r})>"

class Annotations(Base):
    __tablename__ = "lipas_annotations"
    sports_place_id = Column(Integer, ForeignKey("lipas.sports_place_id"), nullable=False, primary_key=True)

    class1_fi = Column(String, unique=False, nullable=True,comment="virma class1")
    class2_fi = Column(String, unique=False, nullable=True,comment="virma class2")
    hidden = Column(Boolean, unique=False, comment="is target hidden. NULL = default hidden")
    
    def __repr__(self):
        return f"Annotations(id={self.sports_place_id!r}, class1_fi={self.class1_fi!r})"

# Returns scores from placeid to virma class1,class2 based on previous classes and uses those for missing annotations
def getAnnotationMappings():
    scorings={}
    with ReadySession() as session:
        session.query(Annotations)
    return scorings

def latestModifiedLipas():
    with ReadySession() as session:
        max = session.query(sqlexpr.max(Lipas.lastModified)).first()
        return max and max[0]# or datetime.now()-timedelta(days=31)

def guessVirmaClasses(typeCode,geomType):
    return

engine=None
def connect():
    global engine,ReadySession
        
    connect_url = sqlalchemy.engine.url.URL.create(
        'postgresql',
        username=config.username,
        password=config.password,
        host=config.host,
        port=5432,
        database = config.db
        )


    engine = create_engine(connect_url, echo=False)

    Base.metadata.create_all(engine)

    ReadySession = sessionmaker(bind=engine)
    #session = Session()




if __name__ == "__main__":
    connect()
    print("latestModifiedLipas()",latestModifiedLipas())