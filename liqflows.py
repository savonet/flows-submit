#!/usr/bin/python
import sys
import os
import json
import pygeoip
import redis
import hashlib
from sqlalchemy import *
from urlparse import urlparse
from datetime import datetime,timedelta
from flask import Flask,request,g
from schema import model
app = Flask(__name__)

def error(res, msg):
  res.status_code = 400
  res.data = msg
  return res

# Parse query string

def q(p):
  return request.args.get(p, None)

# Redis 

def publish(cmd, data):
  msg = { 'cmd' : cmd, 'data': data }
  g.redis.publish("flows", json.JSONEncoder().encode(msg))

# String utilities

def test(s):
  if s == None or s == "":
    return
  else:
    if isinstance(s, unicode):
      s.encode("utf-8")
      s = unicode(s.encode("utf-8").decode("string_escape"), "utf-8")
    else:
      s.decode("utf-8")
      s = s.decode("string_escape")

# DB functions

def user_id(user, create=False):
  row = model.users.select(model.users.c.user == user).execute().fetchone()
  if row == None:
    if create:
      model.users.insert().execute(user=user)
      return user_id(user)
    else:
      return None
  else:
    return row[model.users.c.id]

def user_pass(uid):
  return model.users.select(model.users.c.id == uid).execute().fetchone()[model.users.c.password]

def update_user(uid, user, password, email, ip):
  if user == None or user == "":
    sys.stderr.write("Empty user name!\n")
    raise Exception("Empty user name!")

  if password == None or password == "":
    sys.stderr.write("Empty password!\n")
    raise Exception("Empty password!")

  u = model.users.update(model.users.c.id == uid)
  if email != None: u.execute(email=email)
  password=hashlib.sha224(password).hexdigest()
  u.execute(user=user, password=password, last_seen=datetime.today(), last_ip=ip)

def radio_id(uid, radio, create=False):
  row = model.radios.select((model.radios.c.user_id == uid) & (model.radios.c.name == radio)).execute().fetchone()
  if row == None:
    if not create:
      sys.stderr.write("Error: radio id does not exist while not creating it!\n")
      raise Exception("Radio id does not exist!")
    test(radio)

    model.radios.insert().execute(user_id=uid, name=radio, title=radio)
    id = radio_id(uid, radio)
    publish('add_radio', { "id": id })
    return id
  else:
    id = row[model.radios.c.id]
    return id

def touch_radio(id):
  model.radios.update(model.radios.c.id == id).execute(last_seen=datetime.today())

def update_radio(id, name, website, description, genre, ip=None):
  test(name)
  test(description)
  test(genre)

  if name == None or name == "":
    sys.stderr.write("Radio with empty name!\n")
    raise Exception("Radio with empty name!")

  model.radios.update(model.radios.c.id == id).execute(name=name, website=website, description=description, genre=genre, last_seen=datetime.today())
  if ip != None:
    gi = pygeoip.GeoIP("geoip/GeoIPCity.dat")
    r = gi.record_by_addr(ip)
    msg = { 'id': id, 'name': name, 'website': website, 'description': description, 'genre': genre }
    if r != None:
      latitude  = r['latitude']
      longitude = r['longitude']
      model.radios.update(model.radios.c.id == id).execute(latitude=latitude, longitude=longitude)
      msg.latitude = latitude
      msg.longitude = longitude
    publish('update_radio', msg)

def clear_streams(id):
  model.streams.delete(model.streams.c.radio_id == id).execute()
  publish('clear_streams', { 'id': id }) 

def add_stream(id, url, format, msg):
  test(format)
  test(msg)

  if url == None or url == "":
    sys.stderr.write("Empty url!\n")
    raise Exception("Empty url!")
 
  if format == None or format == "":
    sys.stderr.write("Empty format!\n")
    raise Exception("Empty format!")

  model.streams.insert().execute(radio_id=id, url=url, format=format, msg=msg)
  data = { 'id': id, 'url': url, 'format': format, 'msg': msg }
  publish('add_stream', data)

def metadata(id, artist, title):
  test(artist)
  test(title)

  if title == None or title == "":
    sys.stderr.write("Metadata with empty title!")
    raise Exception("Metadata with empty title!")

  model.radios.update(model.radios.c.id == id).execute(artist=artist, title=title)
  touch_radio(id)
  data = { 'id': id, 'title': title, 'artist': artist }
  publish('metadata', data)

@app.before_request
def before_request():
  db = create_engine(os.environ.get('DATABASE_URL','postgres://localhost:7778/flows'))
  db.echo = False # Enable to debug DB queries
  model.meta.bind = db

  # Open redis
  redis_url = urlparse(os.environ.get('REDISTOGO_URL','redis://localhost:6379'))
  g.redis = redis.Redis(host=redis_url.hostname, port=redis_url.port, password=redis_url.password)

@app.route('/')
def main():
  g.ip = request.remote_addr
  g.version = q("v") # Protocol version
  g.cmd= q("cmd")   # Command
  if g.cmd== None: g.cmd=""

  response = app.make_response("")

  # HTTP headers
  response.headers.add("Content-type", "text/plain")

  # Run command

  radio = q("radio")
  user = q("user")
  if user == None: return error(response, "No user specified.")
  uid = user_id(user)
  password = password=hashlib.sha224(q("password")).hexdigest()
  if uid != None:
    stored_pass =  user_pass(uid)
    if password != stored_pass and password != hashlib.sha224(stored_pass).hexdigest(): return error(response, "Invalid password.")
  if uid == None:
    if (user == "default") & (password == "default"):
        uid = user_id(user, create=True)
    else:
        return error(response, "Unknown user.")
  update_user(uid, user=user, password=q("password"), email=q("email"), ip=g.ip)

  try:
    if g.cmd== "add radio":
      id = radio_id(uid, radio, create=True)
      update_radio(id, name=radio, website=q("radio_website"), description=q("radio_description"), genre=q("radio_genre"), ip=g.ip)
    elif g.cmd== "ping radio":
      id = radio_id(uid, radio)
      touch_radio(id)
    elif g.cmd== "clear streams":
      id = radio_id(uid, radio)
      clear_streams(id)
    elif g.cmd== "add stream":
      id = radio_id(uid, radio)
      add_stream(id, url=q("stream_url"), format=q("stream_format"), msg=q("stream_msg"))
    elif g.cmd== "metadata":
      id = radio_id(uid, radio)
      artist = q("m_artist")
      title  = q("m_title")
      metadata(id, artist, title)
    else:
      return error (response, "Unknown command "+g.cmd+".")

  except:
    return error(response, str(sys.exc_info()[1]))

  response.data = "DONE!"

  return response

if __name__ == '__main__':
  port = int(os.environ.get("PORT", 5000))
  app.debug = True
  app.run(host='0.0.0.0', port=port)
