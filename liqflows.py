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
# load the middleware from werkzeug
# This middleware can be applied to add HTTP proxy support to an application
# that was not designed with HTTP proxies in mind.
# It sets `REMOTE_ADDR`, `HTTP_POST` from `X-Forwarded` headers.
from werkzeug.contrib.fixers import ProxyFix
from schema.model import User, Radio, Stream
app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app)

# Parse query string

def q(p):
  return request.args.get(p, None)

db = create_engine(os.environ.get('DATABASE_URL','postgres://localhost/flows'))
db.echo = False # Enable to debug DB queries
Session = sessionmaker(bind=db)
session = Session()

# Redis
redis_url = urlparse(os.environ.get('REDISTOGO_URL','redis://localhost:6379'))
redis = redis.Redis(host=redis_url.hostname, port=redis_url.port, password=redis_url.password)

def publish(cmd, radio):
  msg = { "cmd": cmd, "radio": radio }
  redis.publish("flows", json.dumps(msg))

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

@app.route('/')
def main():
  g.ip = request.remote_addr
  g.version = q("v") # Protocol version
  g.cmd= q("cmd")   # Command

  response = app.make_response("")

  # HTTP headers
  response.headers.add("Content-type", "text/plain")

  # Run command

  try:
    username = q("user")
    
    if username == None:
      raise Exception("No user given!")

    user     = session.query(User).filter(User.username==username).first()
    password = q("password")
    radio    = session.query(Radio).filter(Radio.name==q("radio")).first()
    
    if radio == None:
      if g.cmd== "add radio": 
        if user == None:
          user  = User(username=username, password=hashlib.sha224(password).hexdigest())
          session.add(user)

        name = q("radio")
        radio = Radio(name=name, title=name, website=q("radio_website"), description=q("radio_description"), genre=q("radio_genre"), user=user)
        session.add(radio)

      else: raise Exception("Radio does not exist!")

    # Special case: if radio user is "default", allow to change it
    # to the newly submitted user.
    if g.cmd == "add radio":
      if radio.user.username == "default":
        if user == None:
          user = User(username=username, password=hashlib.sha224(password).hexdigest())
          session.add(user)
        
        if user.username != "default":
          radio.user = user

    if user == None:
      raise Exception("No such user!")

    if user.password != hashlib.sha224(password).hexdigest():
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
      title = q("m_title")
      if title == None or title == "":
        raise Exception("Empty title!")

      radio.artist = q("m_artist")
      radio.title  = title

    else:
      raise Exception("Unknown command "+g.cmd+".")

    update_radio(radio)
    response.data = { "status": "OK!" }
    publish(g.cmd, radio.export()) 

  except:
    sys.stderr.write("Error: " + str(sys.exc_info()[1]) + "\n")
    response.status_code = 400
    response.data = { "status": str(sys.exc_info()[1]) }

  session.commit()
  response.data = json.dumps(response.data)
  return response

if __name__ == '__main__':
  port = int(os.environ.get("PORT", 5000))
  app.debug = True
  app.run(host='0.0.0.0', port=port)
