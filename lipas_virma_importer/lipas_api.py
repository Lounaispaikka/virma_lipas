from . import config
DEBUG=config.DEBUG

from collections import defaultdict
import logging
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

fromGeoJSONToOurProjection = pyproj.Transformer.from_crs(crs_geojson, crs, always_xy=True).transform


log = logging.getLogger(__name__)
log.setLevel(DEBUG and logging.DEBUG or logging.INFO)
log.info("Starting lipas")
log.debug("Debug logging enabled")

sportsPlaceTypes=None

def sports_place_types(lang='fi'):
        return requests.get(
                        "http://lipas.cc.jyu.fi/api/sports-place-types?lang=fi")

from . import database as db

def toGeoEnum(gtype):
        if gtype=="Point":
                return db.GeometryType.point
        elif gtype=="LineString":
                return db.GeometryType.route
        elif gtype=="Polygon":
                return db.GeometryType.area
        assert False,"invalid geom type"    



params = {
        "lang": "fi",
        "cityCodes":    config.cityCodes, 
        
        # 800 char url limit (header nginx)
        "fields": [
            "lastModified",
        #    "admin",
        #    #"constructionYear",
        #    "email",
            "freeUse",
        #    "location.address",
        #    "location.city.cityCode",
        #    "location.city.name",
        #    "location.coordinates.tm35fin",
        #    "location.coordinates.wgs84",
        #    "location.geometries",
        #    "location.locationId",
        #    "location.neighborhood",
        #    "location.postalCode",
        #    "location.postalOffice",
        #    "location.sportsPlaces",
        #    "name",
        #    "owner",
        #    "phoneNumber",
        #    "properties",
        #    "renovationYears",
        #    "schoolUse",
        #    "type.typeCode",
        #    "www",
        ],
        
}


sports_site_resp_example={
    "properties": {
        "area-m2": 1050,
        "school-use?": True,
        "field-width-m": 25,
        "field-length-m": 42,
        "surface-material": [
            "grass"
        ]
    },
    "email": "vapaa-aikatoimi@pyhajoki.fi",
    "phone-number": "040 359 6104",
    "admin": "city-technical-services",
    "www": "http://www.pyhajoki.fi/",
    "name": "Yppärin koulun luistelukenttä",
    "construction-year": 1989,
    "type": {
        "type-code": 1520
    },
    "lipas-id": 505113,
    "status": "active",
    "event-date": "2014-07-24T08:28:31.435Z",
    "location": {
        "city": {
            "city-code": 625
        },
        "address": "Vanha maantie 39",
        "geometries": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            24.0954877085208,
                            64.4053069505403
                        ]
                    }
                }
            ]
        },
        "postal-code": "86170",
        "postal-office": "Pyhäjoki"
    },
    "owner": "city"
}

from diskcache import FanoutCache
cache = FanoutCache()
@cache.memoize(expire=60*60*24*3, tag='stat_kunta')
def get_stat_classifications_kunta():
    resp=requests.get("https://data.stat.fi/api/classifications/v2/classifications/kunta_1_20230101/classificationItems?content=data&format=json&lang=fi&meta=max")
    resp.raise_for_status()
    data = resp.json()
    classifications={}
    for classification in data:
        code = int(classification["code"])
        assert code not in classifications
        classifications[code]=classification

def get_sports_place(sportsPlaceId):
    resp=requests.get(f'https://lipas.fi/api/sports-sites/{sportsPlaceId}')
    resp.raise_for_status() 
    return resp.json()

def downloadSportsPlacesUpdates(langs,sportsPlaces=None,importModifiedAfter=None):
        params.pop("modifiedAfter", None)
        if importModifiedAfter:
            params["modifiedAfter"]=importModifiedAfter.strftime(config.LIPAS_DATETIME_FORMAT)

        sportsPlaces = sportsPlaces or defaultdict(lambda: [])
        for lang in langs:
                params["lang"] = lang

                # DOCS: http://lipas.cc.jyu.fi/api/index.html#!/Sports32places/get_api_sports_places
                response = requests.get('http://lipas.cc.jyu.fi/api/sports-places',
                                                                params=params)
                response.raise_for_status()
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


def try_parsing_date(text):
    for fmt in (config.LIPAS_DATETIME_FORMAT,config.LIPAS_DATETIME_DELETE_FORMAT):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError('no valid date format found')

def download_deleted_sports_places(since=None):
    #TODO: BUG: Can you undelete IDs?
    # DOCS: http://lipas.cc.jyu.fi/api/index.html
    params={}
    params["since"] = (since or datetime(2020, 1, 1, 0, 0, 0, 0)).strftime(config.LIPAS_DATETIME_FORMAT)

    deletions=[]
    response = requests.get('http://lipas.cc.jyu.fi/api/deleted-sports-places',
                                                    params=params)
    deletions.extend(response.json())
    while response.links.get(
                    'next',
                    None) and response.links['next'] != response.links['last']:
            print("extra")
            response = requests.get(
                    'http://lipas.cc.jyu.fi' +
                    response.links['next']["url"])  # TODO: hardcoded
            deletions.extend(response.json())
    ret={}
    for deletion in deletions:
        deletedAt = try_parsing_date(deletion["deletedAt"])
        sportsPlaceId = deletion["sportsPlaceId"]
        if sportsPlaceId in ret:
            deletedAt_Existing=ret.get(sportsPlaceId)
            deletedAt=max(deletedAt,deletedAt_Existing)

        ret[sportsPlaceId]=deletedAt

    log.info("Got %d deleted sports places (actually %d). Oldest: %s, newest: %s",len(ret),len(deletions),min(ret.values(),default="EMPTY"),max(ret.values(),default="EMPTY"))
    return ret

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
