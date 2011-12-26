from sqlalchemy import *
from migrate import *

meta = MetaData()

streams = Table('streams', meta,
  Column('id', Integer, primary_key=True)
)

listeners = Table('listeners', meta,
  Column('id', Integer, primary_key=True),
  Column('stream_id', Integer, ForeignKey(streams.c.id)),
  Column('longitude', Float),
  Column('latitude', Float),
  Column('ip', Text, nullable=False),
  Column('last_seen', DateTime, nullable=False)
)

def upgrade(migrate_engine):
  meta.bind = migrate_engine

  listeners.create()


def downgrade(migrate_engine):
  meta.bind = migrate_engine

  listeners.drop()
