#! coding: utf-8
# pylint: disable-msg=W0311
from bottle import route, redirect, request, run, jinja2_template, debug, static_file
from simplejson import dumps
import api

@route("/")
def main():
  default = None
  meeting_list = api.meeting_list()
  if meeting_list:
    default = meeting_list[0]
    meeting_list.pop(0)
  return jinja2_template("main.html", default=default, 
                         meeting_list=meeting_list)

@route("/create", method="POST")
def create():
  username = request.params.get("username")
  password = request.params.get("password")
  
  ok = api.check(username, password)
  if ok:
    name = request.params.get("name")
    if not api.is_valid(name):
      return "Choose other name"
    
    attendee_users = request.params.get("to_users").split(",")
    moderator_users = [username]
    meeting_id = api.create_meeting(name, attendee_users, moderator_users)
    if meeting_id:
      url = api.join_meeting(username, password, meeting_id)
      redirect(url)
  return "False"

@route("/join", method="POST")
def join():
  meeting_id = request.params.get("meeting_id")
  username = request.params.get("username")
  password = request.params.get("password")
  ok = api.check(username, password)
  if ok:
    url = api.join_meeting(username, password, meeting_id)
    if url:
      redirect(url)
  return "False"
  

@route("/suggest")
def suggest():
  keyword = request.params.get("q")
  users = api.suggest(keyword)
  users = ["%s|%s" % (username, username) for username in users]
  return "\n".join(users)

@route("/change_password", method=["GET", "POST"])
def change_password():
  if request.method == "GET":
    return jinja2_template("change_password.html")
  else:
    username = request.params.get("username")
    old_password = request.params.get("old_passwd")
    new_passwd = request.params.get("new_passwd")
    retype = request.params.get("retype")
    ok = api.check(username, old_password)
    if ok and new_passwd == retype:
      api.add_user(username, new_passwd)
      return "OK"
    return "False"
      

@route("/static/:filename#.+#")
def static(filename):
  return static_file(filename, root='static')
  
  

if __name__ == "__main__":
  debug(True)
  run(port=9999, server="meinheld")
  
