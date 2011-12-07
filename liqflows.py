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
  row = g.users.select(g.users.c.user == user).execute().fetchone()
  if row == None:
    if create:
      g.users.insert().execute(user=user)
      return user_id(user)
    else:
      return None
  else:
    return row[g.users.c.id]

def user_pass(uid):
  return g.users.select(g.users.c.id == uid).execute().fetchone()[g.users.c.password]

def update_user(uid, user, password, email, ip):
  u = g.users.update(g.users.c.id == uid)
  if email != None: u.execute(email=email)
  password=hashlib.sha224(password).hexdigest()
  u.execute(user=user, password=password, last_seen=datetime.today(), last_ip=ip)

def ensure_metadata(rid):
  if g.metadatas.select(g.metadatas.c.radio_id == rid).execute().fetchone() == None:
    g.metadatas.insert().execute(radio_id=rid)

def clear_metadata(rid):
  if g.metadatas.select(g.metadatas.c.radio_id == rid).execute().fetchone() != None:
    g.metadatas.delete(g.metadatas.c.radio_id == rid).execute()
  g.metadatas.insert().execute(radio_id=rid)

def radio_id(uid, radio, create=False):
  row = g.radios.select((g.radios.c.user_id == uid) & (g.radios.c.name == radio)).execute().fetchone()
  if row == None:
    if not create:
      sys.stderr.write("Error: radio id does not exist while not creating it!\n")
      raise Exception("Radio id does not exist!")
    test(radio)

    g.radios.insert().execute(user_id=uid, name=radio)
    rid = radio_id(uid, radio)
    clear_metadata(rid)
    publish('add_radio', { "id": rid })
    return rid
  else:
    rid = row[g.radios.c.id]
    ensure_metadata(rid)
    return rid

def touch_radio(rid):
  g.radios.update(g.radios.c.id == rid).execute(last_seen=datetime.today())

def update_radio(rid, name, website, description, genre, ip=None):
  test(name)
  test(description)
  test(genre)
  
  if name == None or name == "":
    sys.stderr.write("Radio with empty name!\n")
    raise Exception("Radio with empty name!")

  g.radios.update(g.radios.c.id == rid).execute(name=name, website=website, description=description, genre=genre, last_seen=datetime.today())
  if ip != None:
    gi = pygeoip.GeoIP("geoip/GeoIPCity.dat")
    r = gi.record_by_addr(ip)
    msg = { 'id': rid, 'name': name, 'website': website, 'description': description, 'genre': genre }
    if r != None:
      latitude  = r['latitude']
      longitude = r['longitude']
      g.radios.update(g.radios.c.id == rid).execute(latitude=latitude, longitude=longitude)
      msg.latitude = latitude
      msg.longitude = longitude
    publish('update_radio', msg)

def clear_streams(rid):
  g.streams.delete(g.streams.c.radio_id == rid).execute()
  publish('clear_streams', { 'id': rid }) 

def add_stream(rid, url, format, msg):
  test(format)
  test(msg)
  
  g.streams.insert().execute(radio_id=rid, url=url, format=format, msg=msg)
  data = { 'id': rid, 'url': url, 'format': format, 'msg': msg }
  publish('add_stream', data)

def metadata(rid, artist, title):
  test(artist)
  test(title)
 
  if title == None or title == "":
    sys.stderr.write("Metadata with empty title!")
    raise Exception("Metadata with empty title!")

  clear_metadata(rid)
  g.metadatas.update(g.metadatas.c.radio_id == rid).execute(artist=artist, title=title)
  touch_radio(rid)
  data = { 'id': rid, 'title': title, 'artist': artist }
  publish('metadata', data)

@app.before_request
def before_request():
  g.db = create_engine(os.environ.get('DATABASE_URL','postgres://localhost:7778/flows'))
  g.db.echo = False # Enable to debug DB queries
  g.dbmd = MetaData(g.db)
  g.users = Table('users', g.dbmd, autoload=True)
  g.radios = Table('radios', g.dbmd, autoload=True)
  g.streams = Table('streams', g.dbmd, autoload=True)
  g.metadatas = Table('metadatas', g.dbmd, autoload=True)

  # Open redis
  redis_url = urlparse(os.environ.get('REDISTOGO_URL','redis://localhost:6379'))
  g.redis = redis.Redis(host=redis_url.hostname, port=redis_url.port, password=redis_url.password)

@app.route('/')
def main():
  g.fmt= "text"

  g.ip = request.remote_addr
  g.version = q("v") # Protocol version
  g.cmd= q("cmd")   # Command
  if g.cmd== None: g.cmd=""
  g.fmt= q("fmt")   # Output format
  if g.fmt== None: g.fmt= "text"

  response = app.make_response("")

  # HTTP headers
  response.headers.add("Access-Control-Allow-Origin", "*")
  if g.fmt== "text":
    response.headers.add("Content-type", "text/plain")
  elif g.fmt== "html":
    response.headers.add("Content-type", "text/html")
  elif g.fmt== "json":
    response.headers.add("Content-type", "application/json")

  # Run command

  if (g.cmd== "radios") & ((g.fmt== "text") | (g.fmt== "json")):
    rs = select([g.radios, g.metadatas], (g.metadatas.c.radio_id == g.radios.c.id) & (g.radios.c.last_seen >= (datetime.today() - timedelta(minutes=60)))).order_by(desc(g.radios.c.last_seen)).execute()
    ans = []
    for row in rs:
        st = []
        rs_streams = select([g.streams], g.streams.c.radio_id == row[g.radios.c.id]).execute()
        for stream in rs_streams:
            st.append({"format": stream[g.streams.c.format], "url": stream[g.streams.c.url]})
        genre = row[g.radios.c.genre]
        if genre != None: genre = genre.capitalize()
        radio = {"id": row[g.radios.c.id], "name": row[g.radios.c.name], "website": row[g.radios.c.website], "description": row[g.radios.c.description], "genre": genre, "latitude": row[g.radios.c.latitude], "longitude": row[g.radios.c.longitude], "artist": row[g.metadatas.c.artist], "title": row[g.metadatas.c.title], "streams": st}
        ans.append(radio)
    ans = sorted(ans, key=lambda radio: radio["name"])
    response.data = json.JSONEncoder().encode(ans)
    return response

  if g.fmt== "html":
    response.data = """
<html>
<head>
<title>Liquid flows!</title>
</head>
<body>
<h1>Liquid flows!</h1>
<p>
Some examples
<ul>
<li><a href=\"?fmt=html&cmd=add radio&user=toto3&password=pass&email=x@y.com&x=23&radio=test radio\">Add a radio</a></li>
<li><a href=\"?fmt=html&cmd=add stream&user=toto3&password=pass&email=x@y.com&x=23&radio=test radio&stream_url=http://savonet.sf.net\">Add a stream</a></li>
<li><a href='?fmt=text&cmd=radios'>JSON of radios</a></li>
<li><a href='?fmt=html&cmd=radios'>List radios</a></li>
</ul>
</p>
<form action=\"liqflows.py\" method=\"get\">
Command :
<select name='cmd'>
<option value='radios'>List radios</option>
<option value='add radio'>Add radio</option>
<option value='ping radio'>Ping radio</option>
<option value='clear streams'>Clear streams</option>
<option value='add stream'>Add stream</option>
<option value='metadata'>Metadata</option>
</select>
<br/>
User : <input type=\"text\" name=\"user\" value='bob'/><br/>
Password : <input type=\"text\" name=\"password\" value='pass'/><br/>
Mail : <input type=\"text\" name=\"email\" value='a@b.com'/><br/>
Radio : <input type=\"text\" name=\"radio\" value='Funk online of the future'/><br/>
Radio desc : <input type=\"text\" name=\"radio_description\" value='We want the funk!'/><br/>
Stream url : <input type=\"text\" name=\"stream_url\" value='http://savonet.sf.net/radio'/><br/>
Stream format : <input type=\"text\" name=\"stream_format\" value='dirac'/><br/>
Artist : <input type=\"text\" name=\"m_artist\" value='Johnny Halliday'/><br/>
Title : <input type=\"text\" name=\"m_title\" value='Allumer le feu'/><br/>
<input type=\"submit\" value=\"Submit\" />
</form>
"""

  if g.cmd== "radios":
    rs = g.radios.select().execute()
    response.data = "<table>"
    for row in rs:
        response.data += "<tr>"
        for x in [g.radios.c.user_id, g.radios.c.name, g.radios.c.description, g.radios.c.last_seen]: response.data += "<td>",row[x],"</td>"
        response.data += "</tr>"
    response.data += "</table>"
    return response

  radio = q("radio")

  if g.cmd=="id":
    row = g.radios.select((g.radios.c.name == radio)).execute().fetchone()
    if row == None:
      return error(response, "Invalid radio name") 
    response.data = str(row[g.radios.c.id])
    return response

  user = q("user")
  if g.fmt== "html": response.data = "Query from user<b>", user, "</b><br/>"
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
    if g.fmt== "html": response.data += "Command: " + g.cmd + "<br/>"
    if g.fmt== "text": response.data += "CMD " + g.cmd
    if g.cmd== "add radio":
      rid = radio_id(uid, radio, create=True)
      update_radio(rid, name=radio, website=q("radio_website"), description=q("radio_description"), genre=q("radio_genre"), ip=g.ip)
    elif g.cmd== "ping radio":
      rid = radio_id(uid, radio)
      touch_radio(rid)
    elif g.cmd== "clear streams":
      rid = radio_id(uid, radio)
      clear_streams(rid)
    elif g.cmd== "add stream":
      rid = radio_id(uid, radio)
      add_stream(rid, url=q("stream_url"), format=q("stream_format"), msg=q("stream_msg"))
    elif g.cmd== "metadata":
      rid = radio_id(uid, radio)
      artist = q("m_artist")
      title  = q("m_title")
      if not ((artist == None or artist == "") and (title == None or title == "")):
        metadata(rid, artist, title)
    else:
      return error (response, "Unknown command "+g.cmd+".")

    if g.fmt== "html":
      response.data += "<b>DONE</b>"
    elif g.fmt== "text":
      response.data += " DONE"

  except:
    return error(response, str(sys.exc_info()[1]))

  return response

if __name__ == '__main__':
  port = int(os.environ.get("PORT", 5000))
  app.debug = True
  app.run(host='0.0.0.0', port=port)
