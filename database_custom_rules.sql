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
	la.class2_fi as class2_fi
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
	la.class2_fi as class2_fi
from
	lipas l
left join lipas_annotations la on
	l.sports_place_id = la.sports_place_id
left join lipas_types lt on
	l.type_code = lt.type_code;
comment on view lipas_manage is 'Shows all lipas entries and annotates them with place names, allows managing annotation classses';

CREATE or replace RULE lipas_manage_update AS ON UPDATE TO lipas_manage
DO INSTEAD
UPDATE lipas_annotations  SET class1_fi = new.class1_fi, class2_fi = new.class2_fi
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
	la.class2_fi as class2_fi
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
	la.class2_fi as class2_fi
from
	lipas l
left join lipas_annotations la on
	l.sports_place_id = la.sports_place_id
where
	la.class1_fi <> '' and l.geom_type = 'route'::public."geometrytype" ;
comment on view lipas_routes is 'Shows all classified lipas routes (for geoserver)';