-- TODO: move these to a proper migration

CREATE TYPE public."virma_datasources" AS ENUM (
	'notknown',
	'virma',
	'lipas',
	'openstreetmap');

drop view if exists lipas_all;
create or replace view lipas_all as
select
	l.sports_place_id as sports_place_id,
	l.geom_type as feature_type,
	l.type_code as type_code,
	l.name_fi as name_fi,
	l.geom as geom,
	l.www as www,
	l."owner" as upkeeper,
	l.email as upkeepinfo,
	l.length_m  as length_m,
	la.class1_fi as class1_fi,
	la.class2_fi as class2_fi,
	l.city_code as city_code,
	la.hidden as hidden
from
	lipas l
left join lipas_annotations la on
	l.sports_place_id = la.sports_place_id
where
	la.class1_fi <> '';
comment on view lipas_all is '(unused?) Shows all classified lipas entries';




drop view if exists lipas_manage;
create or replace view lipas_manage as
select
	l.sports_place_id,
	l.geom_type,
	l.type_code as type_code,
	lt.type_name as type_name,
	l.name_fi,
	l.geom,
	l.www,
	l."owner",
	l.email,
	l.length_m,
	la.class1_fi as class1_fi,
	la.class2_fi as class2_fi,
	la.hidden as hidden
from
	lipas l
left join lipas_annotations la on
	l.sports_place_id = la.sports_place_id
left join lipas_types lt on
	l.type_code = lt.type_code;
comment on view lipas_manage is 'Shows all lipas entries and annotates them with place names, allows managing annotation classses';

CREATE or replace RULE lipas_manage_update AS ON UPDATE TO lipas_manage
DO INSTEAD
UPDATE lipas_annotations  SET class1_fi = new.class1_fi, class2_fi = new.class2_fi, hidden = new.hidden
WHERE sports_place_id = old.sports_place_id;




drop view if exists lipas_points;
create or replace view lipas_points as
select
	l.sports_place_id as sports_place_id,
	l.name_fi as name_fi,
	l.geom as geom,
	l.www as www,
	l."owner" as upkeeper,
	l.email as upkeepinfo,
	l.length_m  as length_m,
	la.class1_fi as class1_fi,
	la.class2_fi as class2_fi,
	l.city_code as city_code,
	la.hidden as hidden
from
	lipas l
left join lipas_annotations la on
	l.sports_place_id = la.sports_place_id
where
	la.class1_fi <> '' and l.geom_type = 'point'::public."geometrytype";
comment on view lipas_points is 'Shows all classified lipas points (for geoserver)';




drop view if exists lipas_routes;
create or replace view lipas_routes as
select
	l.sports_place_id as sports_place_id,
	l.name_fi as name_fi,
	l.geom as geom,
	l.www as www,
	l."owner" as upkeeper,
	l.email as upkeepinfo,
	l.length_m  as length_m,
	la.class1_fi as class1_fi,
	la.class2_fi as class2_fi,
	l.city_code as city_code,
	la.hidden as hidden
from
	lipas l
left join lipas_annotations la on
	l.sports_place_id = la.sports_place_id
where
	la.class1_fi <> '' and l.geom_type = 'route'::public."geometrytype" ;
comment on view lipas_routes is 'Shows all classified lipas routes (for geoserver)';





/**************************/

CREATE OR REPLACE VIEW public.routes_combined
AS SELECT r.gid,
    r.geom,
    r.id,
    r.datasource,
    r.class1_fi,
    r.class1_se,
    r.class1_en,
    r.class2_fi,
    r.class2_se,
    r.class2_en,
    r.name_fi,
    r.name_se,
    r.name_en,
    r.municipali,
    r.subregion,
    r.region,
    r.info_fi,
    r.info_se,
    r.info_en,
    r.chall_clas,
    r.length_m,
    r.accessibil,
    r.www_fi,
    r.www_se,
    r.www_en,
    r.email,
    r.telephone,
        CASE
            WHEN r.publicinfo::boolean IS TRUE THEN r.upkeeper
            ELSE NULL::character varying
        END AS upkeeper,
        CASE
            WHEN r.publicinfo::boolean IS TRUE THEN r.upkeepinfo
            ELSE NULL::character varying
        END AS upkeepinfo,
    r.upkeepclas,
    r.shapeestim,
    r.sh_es_date,
    r.sh_es_pers,
    r."timestamp",
    r.updater_id,
    r.special,
    r.munici_nro,
    r.subreg_nro,
    r.region_nro,
    r.publicinfo::boolean AS publicinfo,
    r.picture,
    r.www_picture,
    r.hidden
   FROM routes r
UNION ALL
 SELECT l.gid,
    l.geom,
    l.sports_place_id AS id,
    'lipas'::virma_datasources AS datasource,
    la.class1_fi,
    cc.class1_se,
    cc.class1_en,
    la.class2_fi,
    cc2.class2_se,
    cc2.class2_en,
    l.name_fi,
    NULL::character varying AS name_se,
    NULL::character varying AS name_en,
    NULL::character varying AS municipali,
    NULL::character varying AS subregion,
    NULL::character varying AS region,
    NULL::text AS info_fi,
    NULL::text AS info_se,
    NULL::text AS info_en,
    NULL::text AS chall_clas,
    l.length_m,
    NULL::text AS accessibil,
    l.www AS www_fi,
    NULL::character varying AS www_se,
    NULL::character varying AS www_en,
    l.email,
    NULL::character varying AS telephone,
    NULL::character varying AS upkeeper,
    l.email AS upkeepinfo,
    NULL::character varying AS upkeepclas,
    NULL::character varying AS shapeestim,
    NULL::date AS sh_es_date,
    NULL::character varying AS sh_es_pers,
    NULL::date AS "timestamp",
    NULL::character varying AS updater_id,
    NULL::character varying AS special,
    NULL::character varying AS munici_nro,
    NULL::character varying AS subreg_nro,
    NULL::character varying AS region_nro,
    true AS publicinfo,
    NULL::character varying AS picture,
    NULL::character varying AS www_picture,
    false AS hidden
   FROM lipas l
     LEFT JOIN lipas_annotations la ON l.sports_place_id = la.sports_place_id
     LEFT JOIN class1 cc ON cc.class1_fi::text = la.class1_fi::text
     LEFT JOIN class2 cc2 ON cc2.class2_fi::text = la.class2_fi::text
  WHERE hidden is false and la.class1_fi::text <> ''::text AND l.geom_type = 'route'::geometrytype;
  
 
 
comment on view routes_combined is 'Shows all classified routes public info (for geoserver)';



drop view public.points_combined;
CREATE OR REPLACE VIEW public.points_combined
AS SELECT r.gid,
    r.geom,
    r.id,
    r.datasource,
    r.class1_fi,
    r.class1_se,
    r.class1_en,
    r.class2_fi,
    r.class2_se,
    r.class2_en,
    r.name_fi,
    r.name_se,
    r.name_en,
    r.municipali,
    r.subregion,
    r.region,
    r.info_fi,
    r.info_se,
    r.info_en,
    r.chall_clas,
    r.accessibil,
    r.equipment,
    r.www_fi,
    r.www_se,
    r.www_en,
    r.email,
    r.telephone,
        CASE
            WHEN r.publicinfo::boolean IS TRUE THEN r.upkeeper
            ELSE NULL::character varying
        END AS upkeeper,
        CASE
            WHEN r.publicinfo::boolean IS TRUE THEN r.upkeepinfo
            ELSE NULL::character varying
        END AS upkeepinfo,
    r.upkeepclas,
    r.shapeestim,
    r.sh_es_date,
    r.sh_es_pers,
    r."timestamp",
    r.updater_id,
    r.special,
    r.munici_nro,
    r.subreg_nro,
    r.region_nro,
    r.publicinfo::boolean AS publicinfo,
    r.picture,
    r.www_picture,
    r.hidden
   FROM points r
UNION ALL
 SELECT l.gid,
    l.geom,
    l.sports_place_id AS id,
    'lipas'::virma_datasources AS datasource,
    la.class1_fi,
    cc.class1_se,
    cc.class1_en,
    la.class2_fi,
    cc2.class2_se,
    cc2.class2_en,
    l.name_fi,
    NULL::character varying AS name_se,
    NULL::character varying AS name_en,
    NULL::character varying AS municipali,
    NULL::character varying AS subregion,
    NULL::character varying AS region,
    NULL::text AS info_fi,
    NULL::text AS info_se,
    NULL::text AS info_en,
    NULL::text AS chall_clas,
    NULL::text AS accessibil,
    NULL::text AS equipment,
    l.www AS www_fi,
    NULL::character varying AS www_se,
    NULL::character varying AS www_en,
    l.email,
    NULL::character varying AS telephone,
    NULL::character varying AS upkeeper,
    l.email AS upkeepinfo,
    NULL::character varying AS upkeepclas,
    NULL::character varying AS shapeestim,
    NULL::date AS sh_es_date,
    NULL::character varying AS sh_es_pers,
    NULL::date AS "timestamp",
    NULL::character varying AS updater_id,
    NULL::character varying AS special,
    NULL::character varying AS munici_nro,
    NULL::character varying AS subreg_nro,
    NULL::character varying AS region_nro,
    true AS publicinfo,
    NULL::character varying AS picture,
    NULL::character varying AS www_picture,
    false AS hidden
   FROM lipas l
     LEFT JOIN lipas_annotations la ON l.sports_place_id = la.sports_place_id
     LEFT JOIN class1 cc ON cc.class1_fi::text = la.class1_fi::text
     LEFT JOIN class2 cc2 ON cc2.class2_fi::text = la.class2_fi::text
  WHERE hidden is false AND la.class1_fi::text <> ''::text AND l.geom_type = 'point'::geometrytype;
comment on view points_combined is 'Shows all classified routes (for geoserver)';



GRANT SELECT, UPDATE, INSERT, TRUNCATE, DELETE, TRIGGER, REFERENCES ON TABLE public.routes_combined TO virma;
GRANT SELECT, UPDATE, INSERT, TRUNCATE, DELETE, TRIGGER, REFERENCES ON TABLE public.points_combined TO virma;
GRANT SELECT, UPDATE, INSERT, TRUNCATE, DELETE, TRIGGER, REFERENCES ON TABLE public.lipas_all TO virma;
GRANT SELECT, UPDATE, INSERT, TRUNCATE, DELETE, TRIGGER, REFERENCES ON TABLE public.lipas_manage TO virma;
GRANT SELECT, UPDATE, INSERT, TRUNCATE, DELETE, TRIGGER, REFERENCES ON TABLE public.lipas_annotations TO virma;
GRANT SELECT, UPDATE, INSERT, TRUNCATE, DELETE, TRIGGER, REFERENCES ON TABLE public.lipas_routes TO virma;
GRANT SELECT, UPDATE, INSERT, TRUNCATE, DELETE, TRIGGER, REFERENCES ON TABLE public.lipas_points TO virma;


GRANT SELECT, UPDATE, INSERT, TRUNCATE, DELETE, TRIGGER, REFERENCES ON TABLE public.routes_combined TO datauser;
GRANT SELECT, UPDATE, INSERT, TRUNCATE, DELETE, TRIGGER, REFERENCES ON TABLE public.points_combined TO datauser;
GRANT SELECT, UPDATE, INSERT, TRUNCATE, DELETE, TRIGGER, REFERENCES ON TABLE public.lipas_all TO datauser;
GRANT SELECT, UPDATE, INSERT, TRUNCATE, DELETE, TRIGGER, REFERENCES ON TABLE public.lipas_manage TO datauser;
GRANT SELECT, UPDATE, INSERT, TRUNCATE, DELETE, TRIGGER, REFERENCES ON TABLE public.lipas_annotations TO datauser;
GRANT SELECT, UPDATE, INSERT, TRUNCATE, DELETE, TRIGGER, REFERENCES ON TABLE public.lipas_routes TO datauser;
GRANT SELECT, UPDATE, INSERT, TRUNCATE, DELETE, TRIGGER, REFERENCES ON TABLE public.lipas_points TO datauser;

