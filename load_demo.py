#! /usr/bin/env python
import api
import sys

try:
  username = sys.argv[1]
except IndexError:
  print "Usage: ./useradd foo bar"
try: 
  password = sys.argv[2]
except IndexError:
  password = None
print api.add_user(username, password)