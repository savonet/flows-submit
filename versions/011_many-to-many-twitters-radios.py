from sqlalchemy import *
from migrate import *

meta = MetaData()

radios = Table('radios', meta,
  Column('id', Integer, primary_key=True)
)

twitters = Table('twitters', meta,
  Column('id', Integer, primary_key=True)
)

twitters_radios = Table('twitters_radios', meta,
  Column('radio_id', Integer, ForeignKey('radios.id')),
  Column('twitter_id', Integer, ForeignKey('twitters.id'))
)

def upgrade(migrate_engine):
  meta.bind = migrate_engine

  twitters_radios.create()

  twitters = Table('twitters', meta,
    Column('id', Integer, primary_key=True),
    Column('radio_id', Integer, ForeignKey(radios.c.id)),
    extend_existing=True
  )

  ts = twitters.select().execute()
  for twitter in ts:
    twitters_radios.insert().execute(radio_id=twitter.radio_id,twitter_id=twitter.id)

  twitters.c.radio_id.drop()

def downgrade(migrate_engine):
  meta.bind = migrate_engine

  radio_id = Column('radio_id', Integer, ForeignKey(radios.c.id))

  radio_id.create(twitters)

  rts = twitters_radios.select().execute()
  for assoc in rts:
    twitters.update(id=assoc.twitter_id).execute(radio_id=assoc.radio_id)

  twitters_radios.drop()
