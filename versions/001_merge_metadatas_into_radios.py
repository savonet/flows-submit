from sqlalchemy import *
from migrate import *

meta = MetaData()


metadatas = Table('metadatas', meta,
    Column('radio_id', Integer),
    Column('artist', Text),
    Column('title', Text),
)

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
)

artist_c = Column('artist', Text)
title_c  = Column('title', Text)

def upgrade(migrate_engine):
  meta.bind = migrate_engine
  
  # Add title and artist column to radios table.
  artist_c.create(radios)
  title_c.create(radios)

  # Import old values from metadatas
  ms = metadatas.select().execute()
  for metadata in ms:
    id     = metadata[metadatas.c.radio_id]
    title  = metadata[metadatas.c.title]
    artist = metadata[metadatas.c.artist]
    if title != None:
      radios.update(radios.c.id==id).execute(title=title,artist=artist)  
 
  # Finally drop metadatas table.
  metadatas.drop()

def downgrade(migrate_engine):
  meta.bind = migrate_engine
  
  # Restore metadatas table
  metadatas.create()

  # Import artist and title from radios
  rs = radios.select().execute()
  for radio in rs:
    id     = radio[radios.c.id]
    title  = radio[radios.c.title]
    artist = radio[radios.c.artist]
    metadatas.insert().execute(radio_id=id,title=title,artist=artist)

  # Drop title and artist from radios
  radios.c.title.drop()
  radios.c.artist.drop()
