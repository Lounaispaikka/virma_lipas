"""initial schema

The tables of this project. The views, the rules and the grants of the virma
application are in database_custom_rules.sql, they are not managed here.

Revision ID: 27ebc1b5c13d
Revises:
Create Date: 2026-10-21 14:06:35.427162

"""
import geoalchemy2
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '27ebc1b5c13d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The geometry column needs the postgis extension. It is already installed
    # in the production database, where the notice is harmless.
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # The gid of the lipas table is unique across all the tables of the virma
    # application, so the sequence starts high enough for the other projects
    # of the database.
    op.execute("CREATE SEQUENCE IF NOT EXISTS public.virma_gid_generator AS integer START WITH 300000 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1")
    op.execute("CREATE SEQUENCE IF NOT EXISTS public.class1_id_seq AS integer START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1")
    op.execute("CREATE SEQUENCE IF NOT EXISTS public.class2_id_seq AS integer START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1")
    op.execute("CREATE SEQUENCE IF NOT EXISTS public.lipas_types_type_code_seq AS integer START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1")

    op.create_table('class1',
    sa.Column('id', sa.Integer(), server_default=sa.text("nextval('public.class1_id_seq'::regclass)"), nullable=False),
    sa.Column('class1_fi', sa.String(), nullable=False),
    sa.Column('class1_se', sa.String(), nullable=False),
    sa.Column('class1_en', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('class1_fi', name='class1_pk'),
    sa.UniqueConstraint('class1_se', 'class1_en', 'class1_fi', name='class1_un')
    )
    op.create_table('class2',
    sa.Column('id', sa.Integer(), server_default=sa.text("nextval('public.class2_id_seq'::regclass)"), nullable=False),
    sa.Column('class2_fi', sa.String(), nullable=False),
    sa.Column('class2_se', sa.String(), nullable=False),
    sa.Column('class2_en', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('class2_fi', name='class2_pk'),
    sa.UniqueConstraint('class2_se', 'class2_en', 'class2_fi', name='class2_un')
    )
    op.create_table('lipas_config',
    sa.Column('key', sa.String(), nullable=False, comment='key'),
    sa.Column('str', sa.String(), nullable=True, comment='str val'),
    sa.Column('num', sa.Integer(), nullable=True, comment='num val'),
    sa.Column('date', sa.DateTime(), nullable=True, comment='dateval'),
    sa.PrimaryKeyConstraint('key')
    )
    op.create_table('lipas_types',
    sa.Column('type_code', sa.Integer(), server_default=sa.text("nextval('public.lipas_types_type_code_seq'::regclass)"), nullable=False, comment='typeCode'),
    sa.Column('type_name', sa.String(), nullable=False, comment='typeName'),
    sa.Column('type_name_se', sa.String(), nullable=True, comment='typeName se'),
    sa.Column('type_name_en', sa.String(), nullable=True, comment='typeName en'),
    sa.Column('import', sa.Boolean(), server_default=sa.text('true'), nullable=False, comment='import this type'),
    sa.PrimaryKeyConstraint('type_code')
    )
    op.create_table('lipas',
    sa.Column('sports_place_id', sa.Integer(), autoincrement=False, nullable=False, comment='lipas id'),
    sa.Column('last_modified', sa.DateTime(), server_default=sa.text('now()'), nullable=False, comment='Automatically updated last modified date from lipas'),
    sa.Column('type_code', sa.Integer(), nullable=False, comment='lipas category'),
    sa.Column('city_code', sa.Integer(), nullable=True, comment='cityCode'),
    sa.Column('name_fi', sa.String(), nullable=False, comment='name of place'),
    sa.Column('info_fi', sa.String(), nullable=True, comment='lipas comment'),
    sa.Column('www', sa.String(), nullable=True, comment='webpage'),
    # the srid has to match the EPSG setting of the importer
    sa.Column('geom', geoalchemy2.types.Geometry(srid=3067, dimension=2, spatial_index=False, from_text='ST_GeomFromEWKT', name='geometry', nullable=False), nullable=False, comment='geometry, can be point or (m)linestring/route or possibly an area'),
    sa.Column('geom_type', sa.Enum('point', 'route', 'area', name='geometrytype'), nullable=False, comment='geom column type (possibly redundant)'),
    sa.Column('email', sa.String(), nullable=True, comment='email'),
    sa.Column('owner', sa.String(), nullable=True, comment='owner'),
    sa.Column('telephone', sa.String(), nullable=True, comment='tel'),
    sa.Column('length_m', sa.Integer(), nullable=True, comment='autocalculated length if route'),
    sa.Column('gid', sa.Integer(), server_default=sa.text("nextval('public.virma_gid_generator'::regclass)"), nullable=False, comment='virma gid for uniqueness across all tables'),
    sa.ForeignKeyConstraint(['type_code'], ['lipas_types.type_code'], ),
    sa.PrimaryKeyConstraint('sports_place_id')
    )
    op.create_index('idx_lipas_geom', 'lipas', ['geom'], unique=False, postgresql_using='gist')
    op.create_index('lipas_geom_type_idx', 'lipas', ['geom_type'], unique=False)
    op.create_index('lipas_gid_idx', 'lipas', ['gid'], unique=True)
    op.create_table('lipas_annotations',
    sa.Column('sports_place_id', sa.Integer(), nullable=False),
    sa.Column('class1_fi', sa.String(), nullable=True, comment='virma class1'),
    sa.Column('class2_fi', sa.String(), nullable=True, comment='virma class2'),
    sa.Column('www_picture', sa.String(), nullable=True, comment='show a picture'),
    sa.Column('admin_notes', sa.String(), nullable=True),
    sa.Column('hidden', sa.Boolean(), nullable=True, comment='is target hidden. NULL=not set by admin'),
    sa.ForeignKeyConstraint(['class1_fi'], ['class1.class1_fi'], ),
    sa.ForeignKeyConstraint(['class2_fi'], ['class2.class2_fi'], ),
    sa.ForeignKeyConstraint(['sports_place_id'], ['lipas.sports_place_id'], ),
    sa.PrimaryKeyConstraint('sports_place_id')
    )
    op.create_index('lipas_annotations_class1_fi_idx', 'lipas_annotations', ['class1_fi'], unique=False)
    op.create_index('lipas_annotations_sports_place_id_idx', 'lipas_annotations', ['sports_place_id'], unique=False)

    op.execute("ALTER SEQUENCE public.class1_id_seq OWNED BY public.class1.id")
    op.execute("ALTER SEQUENCE public.class2_id_seq OWNED BY public.class2.id")
    op.execute("ALTER SEQUENCE public.lipas_types_type_code_seq OWNED BY public.lipas_types.type_code")
