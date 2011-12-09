from sqlalchemy import *
from migrate import *
from schema import types
import os

meta = MetaData()

radios = Table('radios', meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user_id', Integer, nullable=False),
    Column('name', Text, unique=True, nullable=False),
    Column('website', Text),
    Column('description', Text),
    Column('genre', Text),
    Column('last_seen', DateTime),
    Column('longitude', Float),
    Column('latitude', Float),
    Column('artist', Text),
    Column('title', Text, nullable=False),
)

token_c = Column('token', types.Token)

def upgrade(migrate_engine):
  meta.bind = migrate_engine

  # Create new row
  token_c.create(radios)

  # Populate it
  rows = radios.select().execute()
  for row in rows:
    radios.update(radios.c.id == row[radios.c.id]).execute(token = os.urandom(20).encode("hex")) 

  # Add constraints
  UniqueConstraint(radios.c.token).create() 
  radios.c.token.alter(nullable=True)


def downgrade(migrate_engine):
  meta.bind = migrate_engine

  # Drop token row..
  radios.c.token.drop()
