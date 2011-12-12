from sqlalchemy import *
from migrate import *

def upgrade(migrate_engine):
  meta = MetaData(bind=migrate_engine)
  users = Table('users', meta,
    Column('user', Text, unique=True, nullable=False)
  )

  users.c.user.alter(name="username")


def downgrade(migrate_engine):
  meta = MetaData(bind=migrate_engine)
  users = Table('users', meta,
    Column('username', Text, unique=True, nullable=False)
  )

  users.c.username.alter(name="user")
