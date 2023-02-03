-- TODO: move these to a proper migration

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
	la.sports_place_id,
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





drop view if exists routes_combined;
create or replace view routes_combined as

(
select
	'virma' as datasource,
	gid,
	geom,
	id,
	class1_fi,
	class1_se,
	class1_en,
	class2_fi,
	class2_se,
	class2_en,
	name_fi,
	name_se,
	name_en,
	municipali,
	subregion,
	region,
	info_fi,
	info_se,
	info_en,
	chall_clas,
	length_m,
	accessibil,
	www_fi,
	www_se,
	www_en,
	email,
	telephone,
	upkeeper,
	upkeepinfo,
	upkeepclas,
	shapeestim,
	sh_es_date,
	sh_es_pers,
	timestamp,
	updater_id,
	special,
	munici_nro,
	subreg_nro,
	region_nro,
	publicinfo,
	picture,
	www_picture,
	hidden
from
	routes r
where
r.hidden = false
  )
  
union all
(
select 
  'lipas' as datasource, 
  l.sports_place_id as gid, 
  l.geom as geom, 
  l.sports_place_id as id, 
  l.class1_fi as class1_fi, 
  cc.class1_se as class1_se,
  cc.class1_en as class1_en, 
  l.class2_fi as class2_fi, 
  cc2.class2_se,
  cc2.class2_en,
  l.name_fi as name_fi, 
  null as name_se, 
  null as name_en, 
  null as municipali, 
  null as subregion, 
  null as region, 
  null as info_fi, 
  null as info_se, 
  null as info_en, 
  null as chall_clas, 
  l.length_m as length_m,
  null as accessibil, 
  l.www as www_fi, 
  null as www_se, 
  null as www_en, 
  l.upkeepinfo as email, 
  null as telephone, 
  null as upkeeper, 
  l.upkeepinfo as upkeepinfo, 
  null as upkeepclas, 
  null as shapeestim, 
  null as sh_es_date, 
  null as sh_es_pers, 
  null as timestamp, 
  null as updater_id, 
  null as special, 
  null as munici_nro, 
  null as subreg_nro, 
  null as region_nro, 
  'T' as publicinfo, 
  null as picture, 
  null as www_picture, 
  false as hidden
from 
  lipas_routes l
left join class1 cc on
cc.class1_fi = l.class1_fi
left join class2 cc2 on
cc2.class2_fi = l.class2_fi
where true );

comment on view routes_combined is 'Shows all classified routes (for geoserver)';






drop view if exists points_combined;
create or replace view points_combined as

(
select
	'virma' as datasource,
	gid,
	geom,
	id,
	class1_fi,
	class1_se,
	class1_en,
	class2_fi,
	class2_se,
	class2_en,
	name_fi,
	name_se,
	name_en,
	municipali,
	subregion,
	region,
	info_fi,
	info_se,
	info_en,
	chall_clas,
	accessibil,
	www_fi,
	www_se,
	www_en,
	email,
	telephone,
	upkeeper,
	upkeepinfo,
	upkeepclas,
	shapeestim,
	sh_es_date,
	sh_es_pers,
	timestamp,
	updater_id,
	special,
	munici_nro,
	subreg_nro,
	region_nro,
	publicinfo,
	picture,
	www_picture,
	hidden
from
	points r
where
r.hidden = false
  )
  
union all
(
select 
  'lipas' as datasource, 
  l.sports_place_id as gid, 
  l.geom as geom, 
  l.sports_place_id as id, 
  l.class1_fi as class1_fi, 
  cc.class1_se as class1_se,
  cc.class1_en as class1_en, 
  l.class2_fi as class2_fi, 
  cc2.class2_se,
  cc2.class2_en,
  l.name_fi as name_fi, 
  null as name_se, 
  null as name_en, 
  null as municipali, 
  null as subregion, 
  null as region, 
  null as info_fi, 
  null as info_se, 
  null as info_en, 
  null as chall_clas, 
  null as accessibil, 
  l.www as www_fi, 
  null as www_se, 
  null as www_en, 
  l.upkeepinfo as email, 
  null as telephone, 
  null as upkeeper, 
  l.upkeepinfo as upkeepinfo, 
  null as upkeepclas, 
  null as shapeestim, 
  null as sh_es_date, 
  null as sh_es_pers, 
  null as timestamp, 
  null as updater_id, 
  null as special, 
  null as munici_nro, 
  null as subreg_nro, 
  null as region_nro, 
  'T' as publicinfo, 
  null as picture, 
  null as www_picture, 
  false as hidden
from 
  lipas_points l
left join class1 cc on
cc.class1_fi = l.class1_fi
left join class2 cc2 on
cc2.class2_fi = l.class2_fi
where true );
comment on view points_combined is 'Shows all classified routes (for geoserver)';