import enum
from . import config
import logging
from functools import lru_cache

import sqlalchemy
from sqlalchemy import Column, Integer, Float, Date
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref
from geoalchemy2 import Geometry
from sqlalchemy.sql import func
from sqlalchemy import Enum
import sqlalchemy.orm.session

#import coloredlogs
log = logging.getLogger(__name__)

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

    typeCode = Column('type_code',Integer, ForeignKey("lipas_types.type_code"), unique=False, nullable=False,comment="lipas category")
    cityCode = Column('city_code',Integer, unique=False, nullable=True,comment="cityCode")
    
    name_fi = Column(String, unique=False, nullable=False,comment="name of place")
    info_fi = Column(String, unique=False, nullable=True,comment="lipas comment")
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
    
    annotation = relationship("Annotations", cascade="all,delete", uselist=False, backref="lipas")
 
    def __repr__(self):
        return f"<LipasMirrorDB (id={self.sports_place_id!r}, name={self.name_fi!r})>"

shapelyTypeToDB={
  "Point": GeometryType.point,
  "point": GeometryType.point,
  "MultiPoint": GeometryType.point,

  "linestring": GeometryType.route,
  "LineString": GeometryType.route,
  "multilinestring": GeometryType.route,
  "MultiLineString": GeometryType.route,

  "MultiPolygon": GeometryType.area,
  "Polygon": GeometryType.area,
}

class VirmaClass1(Base):

    __tablename__ = 'class1'

    id = Column('id',Integer, primary_key=True,comment="typeCode")
    class1_fi = Column('class1_fi',String, unique=False, nullable=False,comment="class1_fi")
    class1_se = Column('class1_se',String, unique=False, nullable=False,comment="class1_se")
    class1_en = Column('class1_en',String, unique=False, nullable=False,comment="class1_en")
    
    def __repr__(self):
        return f"<VirmaClass1 (id={self.typeCode!r}, name={self.class1_fi!r})>"

class VirmaClass2(Base):

    __tablename__ = 'class2'

    id = Column('id',Integer, primary_key=True,comment="typeCode")
    class2_fi = Column('class2_fi',String, unique=False, nullable=False,comment="class2_fi")
    class2_se = Column('class2_se',String, unique=False, nullable=False,comment="class2_se")
    class2_en = Column('class2_en',String, unique=False, nullable=False,comment="class2_en")
    
    def __repr__(self):
        return f"<VirmaClass2 (id={self.typeCode!r}, name={self.class2_fi!r})>"

class LipasTypes(Base):

    __tablename__ = 'lipas_types'

    typeCode = Column('type_code',Integer, primary_key=True,comment="typeCode")
    typeName = Column('type_name',String, unique=False, nullable=False,comment="typeName")
    typeName_se = Column('type_name_se',String, unique=False, nullable=True,comment="typeName se")
    typeName_en = Column('type_name_en',String, unique=False, nullable=True,comment="typeName en")
    
    def __repr__(self):
        return f"<LipasType (id={self.typeCode!r}, name={self.typeName!r})>"

class LipasConfig(Base):

    __tablename__ = 'lipas_config'

    key = Column('key',String, primary_key=True,comment="key")
    val_str = Column('str',String, unique=False, nullable=True,comment="str val")
    val_num = Column('num',Integer, unique=False, nullable=True,comment="num val")
    val_date = Column('date',DateTime, unique=False, nullable=True,comment="dateval")

    def __repr__(self):
        return f"<LipasConfig (key={self.key!r})>"

class Annotations(Base):
    __tablename__ = "lipas_annotations"
    sports_place_id = Column(Integer, ForeignKey("lipas.sports_place_id"), nullable=False, primary_key=True)
    sports_place = relationship('Lipas', backref='lipas_annotations', uselist=False, viewonly=True)

    class1_fi   = Column(String, ForeignKey("class1.class1_fi"), unique=False,  nullable=True,comment="virma class1")
    class2_fi   = Column(String, ForeignKey("class2.class2_fi"), unique=False, nullable=True,comment="virma class2")
    www_picture = Column(String, unique=False, nullable=True,comment="show a picture")
    admin_notes = Column(String, unique=False, nullable=True,comment="")
    hidden      = Column(Boolean, unique=False, nullable=True, comment="is target hidden. NULL=not set by admin")

    def __repr__(self):
        return f"<Annotation (id={self.sports_place_id!r}, class2_fi={self.class2_fi!r})>"


# Returns scores from placeid to virma class1,class2 based on previous classes and uses those for missing annotations

from sqlalchemy import text
statement_get_annotation_scores = text("""
    select
        type_code,
        COUNT(*) as score,
        class1_fi,
        class2_fi

    from
        lipas_annotations
    left join lipas
        on lipas.sports_place_id = lipas_annotations.sports_place_id
    where lipas_annotations.class2_fi is not null
    group by
        class1_fi,
        class2_fi,
        type_code
""")

@lru_cache(maxsize=2)
def get_annotation_scores():
    scorings={}
    with ReadySession() as session:
        #q = session.query(Annotations.class1_fi,Annotations.class2_fi,Lipas.typeCode).select_from(Lipas).join(Lipas.annotation).distinct().filter(Annotations.class2_fi != '')
        for row in session.execute(statement_get_annotation_scores):
            scorelist=scorings.get(row.type_code,[])
            scorings[row.type_code]=scorelist
            scorelist.append(

                {
                    "score": row.score,
                    "class1_fi": row.class1_fi,
                    "class2_fi": row.class2_fi,
                }
             )
    for scorelist in scorings.values():
        scorelist.sort(key=lambda d: ((d.get("class1_fi") and d.get("class2_fi")) and 1 or 0,d['score']), reverse=True)
    return scorings

def guess_annotation_for_type_code(typeCode):
    retlist = get_annotation_scores().get(typeCode)
    if not retlist:
        return
    for ret in retlist:
        if ret.get("class1_fi") and ret.get("class2_fi"):
            return ret
    for ret in retlist:
        if ret.get("class1_fi"):
            return ret
    for ret in retlist:
        if ret.get("class2_fi"):
            return ret

from sqlalchemy.orm import contains_eager
from sqlalchemy import or_

def process_unannotated(session):
    # https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#using-contains-eager-to-load-a-custom-filtered-collection-result
    return  (   
                session.query(Lipas)
                    .join(Lipas.annotation)
                    .filter(or_(Annotations.class2_fi.is_(None),Annotations.class1_fi.is_(None)))
                    .options(contains_eager(Lipas.annotation))
                    .execution_options(populate_existing=True)  
            )

    

def latestModifiedLipas():
    with ReadySession() as session:
        return last_import_time(session)

def latest_delete_query_time(set_latest=None):
    with ReadySession() as session:
        last_deletion_query = session.query(LipasConfig).filter_by(key = 'last_deletion_query').first()
        
        if set_latest:
            print("Setting last_deletion_query %s",set_latest)
            if last_deletion_query:
                last_deletion_query.val_date=set_latest
            else:
                last_deletion_query = LipasConfig(key='last_deletion_query',val_date=set_latest)
                session.add(last_deletion_query)
            session.commit()

        return last_deletion_query and last_deletion_query.val_date


def last_import_time(session,set_latest=None):
    last_import = session.query(LipasConfig).filter_by(key = 'last_import').first()
    
    if set_latest:
        print("Setting last_import %s",set_latest)
        if last_import:
            last_import.val_date=set_latest
        else:
            last_import = LipasConfig(key='last_import',val_date=set_latest)
            session.add(last_import)

    return last_import and last_import.val_date


engine=None
connect_url = sqlalchemy.engine.url.URL.create(
    'postgresql',
    username=config.username,
    password=config.password,
    host=config.host,
    port=5432,
    database = config.db
    )
def connect():
    global engine,ReadySession
    
    engine = create_engine(connect_url, echo=False)

    Base.metadata.create_all(engine)

    ReadySession = sessionmaker(bind=engine)
    #session = Session()



def sports_places_by_id(session: sqlalchemy.orm.session.Session,sports_place_ids):
    query = session.query(Lipas).filter(Lipas.sports_place_id.in_(sports_place_ids))
    return query

if __name__ == "__main__":
    connect()
    print("latestModifiedLipas()",latestModifiedLipas())
    latest_delete_query_time(datetime.now())
    print("latest_delete_query_time()",latest_delete_query_time())
    print(get_annotation_scores())
    print("guess_annotation_for_type_code(4403)",guess_annotation_for_type_code(4403))
