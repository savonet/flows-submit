from sqlalchemy import *
from migrate import *

meta = MetaData()

streams = Table('streams', meta,
    Column('radio_id', Integer),
    Column('format', Text, nullable=False),
    Column('url', Text, nullable=False),
    Column('msg', Text)
)

id_c = Column('id', Integer, primary_key=True)

def upgrade(migrate_engine):
  meta.bind = migrate_engine

  # Create column
  id_c.create(streams, primary_key_name='id')

def downgrade(migrate_engine):
  meta.bind = migrate_engine

  # Drop column
  streams.c.id.drop()
