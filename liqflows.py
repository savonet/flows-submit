#!/usr/bin/python
import sys
import os
import json
import pygeoip
import redis
import hashlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urlparse import urlparse
from datetime import datetime,timedelta
from flask import Flask,request,g
from schema.model import User, Radio, Stream
app = Flask(__name__)

# Parse query string

def q(p):
  return request.args.get(p, None)

# Redis 

def publish(cmd, data):
  msg = { 'cmd' : cmd, 'data': data }
  g.redis.publish("flows", json.dumps(msg))

# Update radio
def update_radio(radio):
  if g.ip != None:
    radio.user.last_ip = g.ip
    gi = pygeoip.GeoIP("geoip/GeoIPCity.dat")
    r = gi.record_by_addr(g.ip)
    if r != None:
      radio.latitude  = r['latitude']
      radio.longitude = r['longitude']

  radio.last_seen = radio.user.last_seen = datetime.today()

@app.before_request
def before_request():
  db = create_engine(os.environ.get('DATABASE_URL','postgres://localhost:7778/flows'))
  db.echo = False # Enable to debug DB queries
  Session = sessionmaker(bind=db)
  g.session = Session()

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
 
  username = q("user")
  user     = g.session.query(User).filter(User.user==username).first() 
  password = q("password")
  radio    = g.session.query(Radio).filter(Radio.name==q("radio")).first()

  try:
    if radio == None:
      # add radio on an existing radio should work
      # if radio belongs to the user.
      if g.cmd== "add radio": 
        if user == None:
          user  = User(user=username, password=password)
          g.session.add(user)

        name = q("radio")
        radio = Radio(name=name, title=name, website=q("radio_website"), description=q("radio_description"), genre=q("radio_genre"), user=user)
        g.session.add(radio)

      else: raise Exception("Radio does not exist!")

    if user == None:
      raise Exception("No user given!")

    if user.password != password and user.password != hashlib.sha224(password).hexdigest():
      raise Exception("Invalid password.")

    if radio.user != user:
      raise Exception("Invalid user.")

    response.headers['X-Flows-Radio-Token'] = radio.token

    if g.cmd == "add radio" or g.cmd == "ping radio":
      pass

    elif g.cmd == "clear streams":
      radio.streams.clear()

    elif g.cmd == "add stream":
      radio.streams.add(Stream(radio=radio, url=q("stream_url"), format=q("stream_format"), msg=q("stream_msg")))
    
    elif g.cmd == "metadata":
      radio.artist = q("m_artist")
      radio.title  = q("m_title")

    else:
      return error (response, "Unknown command "+g.cmd+".")

    update_radio(radio)
    g.session.commit()
    response.data = { "status": "OK!" }
    publish(g.cmd, radio.export()) 

  except:
    sys.stderr.write("Error: " + str(sys.exc_info()[1]) + "\n")
    response.status_code = 400
    response.data = { "status": str(sys.exc_info()[1]) }
    raise

  response.data = json.dumps(response.data)
  return response

if __name__ == '__main__':
  port = int(os.environ.get("PORT", 5000))
  app.debug = True
  app.run(host='0.0.0.0', port=port)
