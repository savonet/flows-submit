from sqlalchemy import *
from migrate import *

meta = MetaData()

radios = Table('radios', meta,
  Column('id', Integer, primary_key=True)
)

twitters = Table('twitters', meta,
  Column('id', Integer, primary_key=True),
  Column('radio_id', Integer, ForeignKey(radios.c.id)),
  Column('name', Text, nullable=False),
  Column('token', Text, nullable=False),
  Column('secret', Text, nullable=False)
)

def upgrade(migrate_engine):
  meta.bind = migrate_engine

  twitters.create()


def downgrade(migrate_engine):
  meta.bind = migrate_engine

  twitters.drop()
