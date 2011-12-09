from sqlalchemy import *
from migrate import *
from migrate.changeset.constraint import CheckConstraint
from schema.types import Token

meta = MetaData()

class NonEmptyConstraint(CheckConstraint):
  def __init__(self,col):
    CheckConstraint.__init__(self, "length(" + str(col.name) + ") > 0", columns=[col])

users = Table('users', meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user', Text, unique=True, nullable=False),
    Column('password', Text, nullable=False),
    Column('email', Text),
    Column('alive', Text),
    Column('last_seen', DateTime),
    Column('last_ip', Text),
)

radios = Table('radios', meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user_id', Integer, ForeignKey(users.c.id), nullable=False),
    Column('name', Text, unique=True, nullable=False),
    Column('token', Token, unique=True, nullable=False),
    Column('website', Text),
    Column('description', Text),
    Column('genre', Text),
    Column('last_seen', DateTime),
    Column('longitude', Float),
    Column('latitude', Float),
    Column('artist', Text),
    Column('title', Text, nullable=False),
)

streams = Table('streams', meta,
    Column('radio_id', Integer, ForeignKey(radios.c.id), nullable=False),
    Column('format', Text, nullable=False),
    Column('url', Text, nullable=False),
    Column('msg', Text),
)

def upgrade(migrate_engine):
  meta.bind = migrate_engine

  # Be even more fascist!
  NonEmptyConstraint(users.c.user).create()
  NonEmptyConstraint(users.c.password).create()
  NonEmptyConstraint(radios.c.name).create()
  NonEmptyConstraint(radios.c.token).create()
  NonEmptyConstraint(radios.c.title).create()
  NonEmptyConstraint(streams.c.format).create()
  NonEmptyConstraint(streams.c.url).create()

def downgrade(migrate_engine):
  meta.bind = migrate_engine

  # Be less fascist..
  NonEmptyConstraint(users.c.user).drop()
  NonEmptyConstraint(users.c.password).drop()
  NonEmptyConstraint(radios.c.name).drop()
  NonEmptyConstraint(radios.c.token).drop()
  NonEmptyConstraint(radios.c.title).drop()
  NonEmptyConstraint(streams.c.format).drop()
  NonEmptyConstraint(streams.c.url).drop()
