from . import config
DEBUG=config.DEBUG
if config.SENTRY_DSN:
    #TODO: BUG: TEST: https://github.com/getsentry/sentry-python/issues/1941#issuecomment-1467873449
    import sentry_sdk
    sentry_sdk.init(config.SENTRY_DSN)

from collections import defaultdict
import logging
from . import lipas_api
import requests, os, sys
from time import time
from datetime import datetime, timedelta
from . import database
from shapely.geometry import asShape
from geoalchemy2.shape import from_shape
from shapely.geometry import shape, GeometryCollection
import pyproj
from geoalchemy2.functions import ST_FlipCoordinates,ST_GeomFromEWKT
from pyproj import CRS
crs = CRS.from_epsg(config.epsg)
crs_geojson = CRS.from_epsg(4326) # CRS84 is equivalent to WGS84 for which the standard EPSG code is EPSG:4326. urn:ogc:def:crs:OGC:1.3:CRS84 

import geojson,json
from shapely.ops import transform
from shapely.ops import linemerge
from shapely.geometry import MultiLineString
fromGeoJSONToOurProjection = pyproj.Transformer.from_crs(crs_geojson, crs, always_xy=True).transform



logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.INFO)

log = logging.getLogger(__name__)
log.setLevel(DEBUG and logging.DEBUG or logging.INFO)
log.info("Starting lipas")
log.debug("Debug logging enabled")

from . import database as db
#TODO: untested, buggy
langs = ["fi"]  #,"sv","en"]

sportsPlaceTypes=None

db.connect()
def buildSportsPlaceTypes():

    for lang in langs:
        sportsPlaceTypes={}
        resp = lipas_api.sports_place_types()
        t={}
        with db.ReadySession.begin() as session:
            for entry in resp.json():
                typeCode=entry["typeCode"]
                geometryType = lipas_api.toGeoEnum(entry["geometryType"])
                t[typeCode]={
                    "name": entry["name"],
                    "geometryType": geometryType,
                    #"description": entry["description"],
                    "subCategory": entry["subCategory"],
                }
                
                lipasType=db.LipasTypes(typeCode=entry["typeCode"],
                                    typeName=entry["name"])#TODO: ,geometryType=geometryType)

                session.merge(lipasType)
        sportsPlaceTypes[lang] = t

        log.info("sportsPlaceTypes count for %s: %d", lang,
                    len(sportsPlaceTypes[lang]))

    return sportsPlaceTypes

def build_stat_classifications_kunta():
    return lipas_api.get_stat_classifications_kunta()

ignored_types = db.get_ignored_lipas_types()
if ignored_types:
    log.info("Import ignoring sport place types: %s",ignored_types)

importModifiedAfter = db.latestModifiedLipas() 
if importModifiedAfter:
    # TODO: Maybe excessive safety margin
    importModifiedAfter = importModifiedAfter-timedelta(days=1)
elif DEBUG:
    log.error("EMPTY DATABASE: Requesting at most only 30 days of changed data for testing only!!")
    importModifiedAfter= datetime.now()-timedelta(days=30)

def processPlace(place, lang,session):
    sports_place_id = place["sportsPlaceId"]

    typeCode = place["type"]["typeCode"]
    if ignored_types and typeCode in ignored_types:
        return
    

    typeinfo = sportsPlaceTypes[lang][typeCode]


    typeName = typeinfo["name"]
    geometryType = typeinfo["geometryType"]
    # Areas are not supported (2023 decision, Lounaistieto)
    if geometryType == db.GeometryType.area:
        return

    # Download additional info from new undocumented API
    sportsPlaceMeta = lipas_api.get_sports_place(place["sportsPlaceId"])
    place.update(sportsPlaceMeta)


    if not place.get("freeUse", True) and config.onlyFreeUse:
        return #TODO: BUG: freeUse flag might be toggled after initial run, won't remove alreayd imported data currently and stops updating it

    # check that undocumented ids match
    assert place["lipas-id"]==sports_place_id

    loc = place["location"]
    geometries = loc["geometries"]
    www = place.get("www")
    name = place["name"]
    comment = place.get("comment")
    length_m = place.get("properties",{}).get("route-length-km")
    if length_m:
        length_m=length_m*1000


    # geojson cannot load tables, we must redump our data
    geomFeature=geojson.loads(json.dumps(geometries))
    
    assert geomFeature.is_valid,str(geomFeature.errors())
    
    
    if geometryType == db.GeometryType.route:
        # merge linestrings to multilinestring
        shaped = MultiLineString([transform(fromGeoJSONToOurProjection, shape(f.geometry)) for f in geomFeature.features])
    else:

        geometry = geomFeature[0]["geometry"]
        assert len(geomFeature.features)==1
        shaped = transform(fromGeoJSONToOurProjection, shape(geometry))
        
    # GeoJSON and PSQL coordinate orders are different 

    # sports_place_id=510679
    # POINT (3054753 4041473) AFRICA?? BAD
    # POINT (311176  6698723) ANOTHER EXAMPLE? Straight from Lipas
    # POINT (222780  6734461) EXAMPLE OK
    #geom = ST_FlipCoordinates(ST_GeomFromEWKT(from_shape(shaped)))
    
    # Make sure we are still what we say we are
    geomType = db.shapelyTypeToDB[shaped.type]
    assert geometryType==geomType

    geom = from_shape(shaped,config.epsg)

    lastModified = datetime.strptime(place["lastModified"],
                                     config.LIPAS_DATETIME_FORMAT)
    
    
    sportsPlace = db.Lipas(sports_place_id=sports_place_id,
                            name_fi=name,
                            www=www,
                            geom=geom,
                            cityCode = place["location"]["city"]["city-code"],
                            geomType=geomType,
                            length_m = length_m,
                            lastModified=lastModified,
                            info_fi = comment,
                            email=place.get("email"),
                            owner=place.get("admin"),
                            telephone=place.get("phone-number"),
                            typeCode=typeCode)
    session.merge(sportsPlace)
    
    #TODO: Infer class1,class2 based on previous classes
    #TODO: allow unclassified to be reclassified based on new classifications done by user
    sportsPlaceAnnotation = session.query(db.Annotations).filter(db.Annotations.sports_place_id == sports_place_id).first()
    if not sportsPlaceAnnotation:
        guess = database.guess_annotation_for_type_code(typeCode) or {}
        sportsPlaceAnnotation = db.Annotations(sports_place_id=sports_place_id,class1_fi=guess.get("class1_fi"),class2_fi=guess.get("class2_fi"))
        session.add(sportsPlaceAnnotation)

def processSportPlaces(sportsPlaces):
    # TODO: BUG: we risk skipping lipas entries without full sync, because relying  on lastModified. Use 
    # NOTE: Has to be sessioned in language level due to above
    with db.ReadySession() as session:
        lastModifiedMax=None
        for lang in langs:    
            total=None
            for idx,sportsPlace in enumerate(sportsPlaces[lang]):
                processPlace(sportsPlace, lang,session)

                lastModified = sportsPlace["lastModified"]
                lastModifiedMax=max(lastModifiedMax or lastModified,lastModified)

                if idx%100==0:
                    log.debug("Processing: So far processed %d places for language %s",idx+1,lang)
                    session.commit()
                total=idx
            log.debug("Finished processing %d places for language %s",idx+1,lang)
        db.last_import_time(session,lastModifiedMax)
        session.commit()


def run_annotation_guesses():
  with db.ReadySession() as session:
    for res in db.process_unannotated(session):
        new_annotation = db.guess_annotation_for_type_code(res.typeCode)
        if new_annotation and new_annotation.get("class1_fi") and new_annotation.get("class2_fi"):
            log.info("%s wants to be %s",res.name_fi,new_annotation)
            res.annotation.class1_fi = new_annotation["class1_fi"]
            res.annotation.class2_fi = new_annotation["class2_fi"]
    session.commit()

def delete_removed_sport_places():
    latest_delete_query_time = db.latest_delete_query_time()
    deletions = lipas_api.download_deleted_sports_places(latest_delete_query_time)
    latest_delete_query_time=deletions and max(deletions.values()) or latest_delete_query_time
    with db.ReadySession() as session:
        potentially_deleted=db.sports_places_by_id(session,list(deletions.keys())+[])
        for sportsPlace in potentially_deleted:
            deletedAt = deletions[sportsPlace.sports_place_id]
            if deletedAt > sportsPlace.lastModified:
                log.warning("Deleting %s",sportsPlace.sports_place_id)
                session.delete(sportsPlace)
        session.commit()
        db.latest_delete_query_time(latest_delete_query_time)
        session.commit()
        
def main():
    #print("download_deleted_sports_places",len(lipas_api.download_deleted_sports_places()))
    
    log.info("Running delete_removed_sport_places()")
    delete_removed_sport_places()
    
    global sportsPlaceTypes
    log.info("Running buildSportsPlaceTypes()")
    sportsPlaceTypes = buildSportsPlaceTypes()
    log.info("Running build_stat_classifications_kunta()")
    stat_class = build_stat_classifications_kunta()
    log.info("Running downloadSportsPlacesUpdates(%s,after %s)",langs,importModifiedAfter)
    sportsPlaces = lipas_api.downloadSportsPlacesUpdates(langs,importModifiedAfter=None if config.FULL_UPDATE else importModifiedAfter)
    
    log.info("Running processSportPlaces()")
    processSportPlaces(sportsPlaces)
    
    log.info("Running run_annotation_guesses()")
    run_annotation_guesses()

    log.info("Finished")

#main()
#sppi=downloadSportsPlaceIDs()
#print(sppi)
