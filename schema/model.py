import hashlib, os
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from schema.types import Token, NonEmptyConstraint

Base = declarative_base()

class User(Base):
  __tablename__ = 'users'
  id            = Column(Integer, primary_key=True)
  user          = Column(Text, NonEmptyConstraint('user'), unique=True, nullable=False)
  password      = Column(Text, NonEmptyConstraint('password'), nullable=False)
  email         = Column(Text)
  radios        = relationship('Radio', collection_class=set, backref=backref('user'))
  last_seen     = Column(DateTime)
  last_ip       = Column(Text)

  def __init__(self, **args):
    if (not 'password' in args) or args['password'] == None or args['password'] == "":
      raise Exception("Empty password!")
    if (not 'user' in args) or args['user'] == None or args['user'] == "":
      raise Exception("Empty user!")

    args['password'] = hashlib.sha224(args['password']).hexdigest() 

    Base.__init__(self, **args)

  def export(self):
    return { "user"  : self.user, "email" : self.email }

class Radio(Base):
  __tablename__ = 'radios'
  id            = Column(Integer, primary_key=True)
  user_id       = Column(Integer, ForeignKey(User.id))
  name          = Column(Text, NonEmptyConstraint('name'), unique=True, nullable=False)
  token         = Column(Token, NonEmptyConstraint('token'), unique=True, nullable=False)
  website       = Column(Text)
  description   = Column(Text)
  genre         = Column(Text)
  last_seen     = Column(DateTime)
  longitude     = Column(Float)
  latitude      = Column(Float)
  artist        = Column(Text)
  title         = Column(Text, NonEmptyConstraint('title'), nullable=False)
  streams       = relationship('Stream', collection_class=set, backref=backref('radio'), cascade='all, delete-orphan')

  def __init__(self, **args):
    if (not 'name' in args) or args['name'] == None or args['name'] == "":
      raise Exception("Empty radio name!")
    if (not 'title' in args) or args['title'] == None or args['title'] == "":
      raise Exception("Empty radio title!")
    if (not 'user' in args) or args['user'] == None:
      raise Exception("No radio user!")

    if (not 'token' in args) or args['token'] == None:
      args['token'] = os.urandom(20).encode("hex")

    Base.__init__(self, **args)

  def export(self):
    data = { "name" : self.name, "token": self.token, "title" : self.title }
    if self.website != None and self.website != "":
      data["website"] = self.website
    if self.description != None and self.description != "":
      data["description"] = self.description
    if self.genre != None and self.genre != "":
      data["genre"] = self.genre
    if self.longitude != None:
      data["longitude"] = self.website
    if self.latitude != None:
      data["latitude"] = self.website
    if self.artist != None and self.artist != "":
      data["artist"] = self.artist

    data["streams"] = []
    for stream in self.streams:
      data["streams"].append(stream.export())

    return data

class Stream(Base):
  __tablename__ = 'streams' 
  id            = Column(Integer, primary_key=True)
  radio_id      = Column(Integer, ForeignKey(Radio.id))
  format        = Column(Text, NonEmptyConstraint('format'), nullable=False)
  url           = Column(Text, NonEmptyConstraint('url'), nullable=False)
  msg           = Column(Text)

  def __init__(self, **args):
    if (not 'radio' in args) or args['radio'] == None:
      raise Exception("No radio for that stream!")
    if (not 'format' in args) or args['format'] == None or args['format'] == "":
      raise Exception("Empty stream format!")
    if (not 'url' in args) or args['url'] == None or args['url'] == "":
      raise Exception("Empty stream url!")

    Base.__init__(self, **args)

  # Do not export "radio", "streams" is already exported there..
  def export(self):
    data = { "format" : self.format, "url" : self.url }
    if self.msg != None and self.msg != "":
      data["msg"] = self.msg

    return data
