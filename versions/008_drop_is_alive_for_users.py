from sqlalchemy import *
from migrate import *

def upgrade(migrate_engine):
  meta = MetaData()
  meta.bind = migrate_engine

  users = Table('users', meta,
    Column('alive', Text),
  )
  users.c.alive.drop()


def downgrade(migrate_engine):
  meta = MetaData()
  meta.bind = migrate_engine

  users = Table('users', meta)
  alive = Column('alive', Text)

  alive.create(users)
