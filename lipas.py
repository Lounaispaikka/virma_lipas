import config
DEBUG=config.DEBUG

from collections import defaultdict
import logging
import requests, os, sys
from time import time
from datetime import datetime, timedelta
import database
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

fromGeoJSONToOurProjection = pyproj.Transformer.from_crs(crs_geojson, crs, always_xy=True).transform



logging.basicConfig(format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.INFO)

log = logging.getLogger(__name__)
log.setLevel(DEBUG and logging.DEBUG or logging.INFO)
log.info("Starting lipas")
log.debug("Debug logging enabled")

import database as db
langs = ["fi"]  #,"sv","en"]

sportsPlaceTypes=None

db.connect()
def buildSportsPlaceTypes():

    for lang in langs:
        sportsPlaceTypes={}
        resp = requests.get(
            "http://lipas.cc.jyu.fi/api/sports-place-types?lang=fi")
        t={}
        with db.ReadySession.begin() as session:
            for entry in resp.json():
                typeCode=entry["typeCode"]
                t[typeCode]={
                    "name": entry["name"],
                    "geometryType": toGeoEnum(entry["geometryType"]),
                    #"description": entry["description"],
                    "subCategory": entry["subCategory"],
                }
                #lipasType = session.query(db.LipasTypes).filter(db.LipasTypes.typeCode == typeCode).first()
                #if lipasType:
            #     lipasType.typeName=entry["name"]
                #else:
                lipasType=db.LipasTypes(typeCode=entry["typeCode"],
                                    typeName=entry["name"])

                session.merge(lipasType)
        sportsPlaceTypes[lang] = t

        log.info("sportsPlaceTypes count for %s: %d", lang,
                    len(sportsPlaceTypes[lang]))

    return sportsPlaceTypes

def toGeoEnum(gtype):
    if gtype=="Point":
        return db.GeometryType.point
    elif gtype=="LineString":
        return db.GeometryType.route
    elif gtype=="Polygon":
        return db.GeometryType.area
    assert False,"invalid geom type"    

params = {
    "lang":
    "fi",
    "cityCodes":
    config.cityCodes,
    "fields": [
        "admin",
        #"constructionYear",
        "email",
        "freeUse",
        "lastModified",
        "location.address",
        "location.city.cityCode",
        "location.city.name",
        "location.coordinates.tm35fin",
        "location.coordinates.wgs84",
        "location.geometries",
        "location.locationId",
        "location.neighborhood",
        "location.postalCode",
        "location.postalOffice",
        "location.sportsPlaces",
        "name",
        "owner",
        "phoneNumber",
        "properties",
        "renovationYears",
        "schoolUse",
        "type.typeCode",
        "www",
    ],
    
}

latestModifiedAfter = db.latestModifiedLipas() 
# Maybe excessive safety margin
if latestModifiedAfter:
    latestModifiedAfter = latestModifiedAfter-timedelta(days=30)
    params["modifiedAfter"]= latestModifiedAfter.strftime(config.LIPAS_DATETIME_FORMAT)
elif DEBUG:
    logging.error("EMPTY DATABASE: Requesting at most only 30 days of changed data for testing only!!")
    #params["modifiedAfter"]= (datetime.now()-timedelta(days=31)).strftime(config.LIPAS_DATETIME_FORMAT)

def downloadSportsPlacesUpdates(sportsPlaces=None):
    sportsPlaces = sportsPlaces or defaultdict(lambda: [])
    for lang in langs:
        params["lang"] = lang

        # DOCS: http://lipas.cc.jyu.fi/api/index.html#!/Sports32places/get_api_sports_places
        response = requests.get('http://lipas.cc.jyu.fi/api/sports-places',
                                params=params)
        sportsPlaces[lang].extend(response.json())
        while response.links.get(
                'next',
                None) and response.links['next'] != response.links['last']:
            response = requests.get(
                'http://lipas.cc.jyu.fi' +
                response.links['next']["url"])  # TODO: hardcoded
            sportsPlaces[lang].extend(response.json())
        log.info("Got %d sports places for %s", len(sportsPlaces[lang]),
                     lang)
    return sportsPlaces

json_example=json.loads("""{
  "properties": {
    "parkingPlace": true
  },
  "email": "ymparistotoimi@salo.fi",
  "admin": "Kunta / muu",
  "www": "http://www.salo.fi/ymparistojaluonto/luontojaretkeily/luontokohteetjareitit/",
  "name": "Aneriojärven polkujen lähtöpiste",
  "type": {
    "typeCode": 207,
    "name": "Opastuspiste"
  },
  "freeUse": true,
  "lastModified": "2022-10-24 09:00:51.695",
  "sportsPlaceId": 510679,
  "phoneNumber": "02 7781",
  "location": {
    "coordinates": {
      "wgs84": {
        "lon": 23.574236763903,
        "lat": 60.3807325684595
      },
      "tm35fin": {
        "lon": 311176.25,
        "lat": 6698723.25
      }
    },
    "sportsPlaces": [
      510679
    ],
    "address": "Helsingintie 2550",
    "geometries": {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "geometry": {
            "coordinates": [
              23.574236763903,
              60.3807325684595
            ],
            "type": "Point"
          },
          "properties": {
            "pointId": 613712
          }
        }
      ]
    },
    "locationId": 627585,
    "postalCode": "25410",
    "postalOffice": "Suomusjärvi",
    "city": {
      "name": "Salo",
      "cityCode": 734
    }
  },
  "owner": "Kunta"
}""")
shapelyTypeToDB={
  "Point": db.GeometryType.point,
  "point": db.GeometryType.point,
  "MultiPoint": db.GeometryType.point,

  "linestring": db.GeometryType.route,
  "LineString": db.GeometryType.route,
  "multilinestring": db.GeometryType.route,
  "MultiLineString": db.GeometryType.route,

  "MultiPolygon": db.GeometryType.area,
  "Polygon": db.GeometryType.area,
}
def processPlace(place, lang,session):
    if not place.get("freeUse", True) and config.onlyFreeUse:
        return

    loc = place["location"]
    geometries = loc["geometries"]
    sports_place_id = place["sportsPlaceId"]
    www = place.get("www")
    name = place["name"]
    typeCode = place["type"]["typeCode"]
    typeinfo = sportsPlaceTypes[lang][typeCode]
    #test
    typeName = typeinfo["name"]

    geomFeature=geojson.loads(json.dumps(geometries))
    assert geomFeature.is_valid,str(geomFeature.errors())
    #
    geometry = geomFeature[0]["geometry"]
    shaped = transform(fromGeoJSONToOurProjection, shape(geometry))
    
    # GeoJSON and PSQL coordinate orders are different 

    # sports_place_id=510679
    # POINT (3054753 4041473) AFRICA?? BAD
    # POINT (311176  6698723) ANOTHER EXAMPLE? Straight from Lipas
    # POINT (222780  6734461) EXAMPLE OK
    #geom = ST_FlipCoordinates(ST_GeomFromEWKT(from_shape(shaped)))
    
    geomType = shapelyTypeToDB[shaped.type]
    geom = from_shape(shaped,config.epsg)

    lastModified = datetime.strptime(place["lastModified"],
                                     config.LIPAS_DATETIME_FORMAT)
    
    
    sportsPlace = db.Lipas(sports_place_id=sports_place_id,
                            name_fi=name,
                            www=www,
                            geom=geom,
                            cityCode = place["location"]["city"]["cityCode"],
                            geomType=geomType,
                            lastModified=lastModified,
                            email=place.get("email"),
                            owner=place.get("admin"),
                            telephone=place.get("phoneNUmber"),
                            typeCode=typeCode)
    session.merge(sportsPlace)
    
    #TODO: Infer class1,class2 based on previous classes
    #TODO: allow unclassified to be reclassified based on new classifications done by user
    sportsPlaceAnnotation = session.query(db.Annotations).filter(db.Annotations.sports_place_id == sports_place_id).first()
    if not sportsPlaceAnnotation:
        guess_classes = database.guessVirmaClasses(geomType,typeCode)
        class1,class2 = None,None
        if guess_classes:
          class1,class2 = guess_classes

        sportsPlaceAnnotation = db.Annotations(sports_place_id=sports_place_id)
        session.add(sportsPlaceAnnotation)

def processSportPlaces(sportsPlaces):
    # TODO: lastModified should only be updated after all languages have been updated
    # NOTE: Has to be sessioned in language level due to above
    with db.ReadySession.begin() as session:
        for lang in langs:    
            total=None
            for idx,sportsPlace in enumerate(sportsPlaces[lang]):
                processPlace(sportsPlace, lang,session)
                if idx%100==0:
                  log.debug("Processing: So far processed %d places for language %s",idx+1,lang)
                total=idx
            log.debug("Finished processing %d places for language %s",idx+1,lang)

def runReclassification():
  raise NotImplementedError

def main():
    global sportsPlaceTypes
    log.debug("Running buildSportsPlaceTypes()")
    sportsPlaceTypes = buildSportsPlaceTypes()
    log.debug("Running downloadSportsPlacesUpdates()")
    sportsPlaces = downloadSportsPlacesUpdates()
    log.debug("Running processSportPlaces()")
    processSportPlaces(sportsPlaces)
    log.debug("Finished")

main()
