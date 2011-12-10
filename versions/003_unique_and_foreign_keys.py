from sqlalchemy import *
from migrate import *

meta = MetaData()

radios = Table('radios', meta, 
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user_id', Integer),
    Column('name', Text),
    Column('website', Text),
    Column('description', Text),
    Column('genre', Text),
    Column('last_seen', DateTime),
    Column('longitude', Float),
    Column('latitude', Float),
    Column('artist', Text),
    Column('title', Text)
)

users = Table('users', meta, 
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user', Text),
    Column('password', Text),
    Column('email', Text),
    Column('alive', Text),
    Column('last_seen', DateTime),
    Column('last_ip', Text)
)

streams = Table('streams', meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('radio_id', Integer),
    Column('format', Text, nullable=False),
    Column('url', Text, nullable=False),
    Column('msg', Text)
)

# Check if all columns match a foreign
# key and drop it if not.

def check_foreign(source, dest):
  rows = source.table.select().execute()

  for row in rows:
    key = row[source]
    foreign = dest.table.select(dest == key).execute().fetchone()
    if foreign == None:
      source.table.delete(source == key).execute()

def upgrade(migrate_engine):
  meta.bind = migrate_engine

  # Add uniqueness and foreign keys
  UniqueConstraint(radios.c.name).create()
  UniqueConstraint(users.c.user).create()

  check_foreign(radios.c.user_id, users.c.id)
  ForeignKeyConstraint(columns=[radios.c.user_id],refcolumns=[users.c.id]).create()
  
  check_foreign(streams.c.radio_id, radios.c.id)
  ForeignKeyConstraint(columns=[streams.c.radio_id],refcolumns=[radios.c.id]).create()

def downgrade(migrate_engine):
  meta.bind = migrate_engine

  # Drop uniqueness and foreign keys..
  UniqueConstraint(radios.c.name).drop()
  UniqueConstraint(users.c.user).drop()
  ForeignKeyConstraint(columns=[radios.c.user_id],refcolumns=[users.c.id]).drop()
  ForeignKeyConstraint(columns=[streams.c.radio_id],refcolumns=[radios.c.id]).drop()
