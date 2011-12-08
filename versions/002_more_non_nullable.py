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
    Column('title', Text),
)

streams = Table('streams', meta,
    Column('radio_id', Integer),
    Column('format', Text),
    Column('url', Text),
    Column('msg', Text),
)

users = Table('users', meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user', Text),
    Column('password', Text),
    Column('email', Text),
    Column('alive', Text),
    Column('last_seen', DateTime),
    Column('last_ip', Text),
)

# Make columns non nullable and drop
# any null value before.
def alter_non_null(table, columns):
  for column in columns:
    table.delete(column==None).execute()
    
    # Also delete column with empty strings while we're at it..
    try:
      table.delete(column=="").execute()
    except:
      pass

    column.alter(nullable=False)

def upgrade(migrate_engine):
  meta.bind = migrate_engine

  # Be more fascist about some fields..

  alter_non_null(radios, [radios.c.user_id, radios.c.name,radios.c.title])
  alter_non_null(streams, [streams.c.format, streams.c.url])
  alter_non_null(users, [users.c.user, users.c.password])

def downgrade(migrate_engine):
  meta.bind = migrate_engine

  # Be less fascist about some fields..

  radios.c.user_id.alter(nullable=True)
  radios.c.name.alter(nullable=True)
  radios.c.title.alter(nullable=True)
  streams.c.format.alter(nullable=True)
  streams.c.url.alter(nullable=True)
  users.c.user.alter(nullable=True)
  users.c.password.alter(nullable=True)
  users.c.email.alter(nullable=True)
