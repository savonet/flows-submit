from sqlalchemy import *
from schema.types import Token, NonEmptyConstraint
meta = MetaData()

users = Table('users', meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user', Text, NonEmptyConstraint('user'), unique=True, nullable=False),
    Column('password', Text, NonEmptyConstraint('password'), nullable=False),
    Column('email', Text),
    Column('alive', Text),
    Column('last_seen', DateTime),
    Column('last_ip', Text),
)

radios = Table('radios', meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user_id', Integer, ForeignKey(users.c.id), nullable=False),
    Column('name', Text, NonEmptyConstraint('name'), unique=True, nullable=False),
    Column('token', Token, NonEmptyConstraint('token'), unique=True, nullable=False),
    Column('website', Text),
    Column('description', Text),
    Column('genre', Text),
    Column('last_seen', DateTime),
    Column('longitude', Float),
    Column('latitude', Float),
    Column('artist', Text),
    Column('title', Text, NonEmptyConstraint('title'), nullable=False),
)

streams = Table('streams', meta,
    Column('radio_id', Integer, ForeignKey(radios.c.id), nullable=False),
    Column('format', Text, NonEmptyConstraint('format'), nullable=False),
    Column('url', Text, NonEmptyConstraint('url'), nullable=False),
    Column('msg', Text),
)
