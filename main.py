#! coding: utf-8
# pylint: disable-msg=W0311
from bottle import route, redirect, request, run, jinja2_template, \
                    debug, static_file, response
import api
import settings

# unicode
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
# end hack

@route("/_edit", method=["GET", "POST"])
def edit():
  username = request.get_cookie("username", settings.cookie_secret)
  password = request.get_cookie("password", settings.cookie_secret)
  ok = api.check(username, password)
  if ok:
    username = username.lower()
    if request.method == "GET":
      meeting_id = request.params.get("meeting_id")
      info = api.get_meeting_info(meeting_id)
      
      if username not in info.get("moderator_users") and username not in settings.admins:
        redirect("/start")
      
      users = api.suggest("")
      
#      username = username.lower()
#      if username in users:
#        users.remove(username)
      attendee_users = info.get("attendee_users")
      if "" in info.get("attendee_users"):
        attendee_users.remove("")
      
      attendee_users = [x.strip() for x in attendee_users]  # remove start/end space
      
      if username not in attendee_users:
        attendee_users.append(username)
      
      info['attendee_users'] = attendee_users
      
      users = [x for x in users if x not in attendee_users]

      return jinja2_template('edit.html', 
                             users=users,
                             info=info)
    else:
      meeting_id = request.params.get("meeting_id")
      name = request.params.get("name")
      attendee_users = request.params.get("attendee_users").split(",")
      attendee_users = [x.strip() for x in attendee_users if x != ""]
      api.update(username, meeting_id, name, attendee_users)
      redirect('/start')
    

@route("/_delete", method="POST")
def delete():
  username = request.get_cookie("username", settings.cookie_secret)
  password = request.get_cookie("password", settings.cookie_secret)
  ok = api.check(username, password)
  if ok:
    meeting_id = request.params.get("meeting_id")
    if username in settings.admins:
      api.remove(meeting_id)
    else:
      info = api.get_meeting_info(meeting_id)
      if username in info.get("moderator_users"):
        api.remove(meeting_id)
  redirect("/start")
      
  
@route("/")
@route("/start")
def main():
  username = request.get_cookie("username", settings.cookie_secret)
  password = request.get_cookie("password", settings.cookie_secret)
  ok = api.check(username, password)
  if not ok:
    redirect("/login")
  meeting_list = api.meeting_list()

  owners = []
  for meeting in meeting_list:
    if username.lower() in settings.admins or username.lower() in meeting.get("moderator_users"):
      owners.append(meeting)
    is_running = api.is_running(meeting.get('id'))
    if is_running:
      meeting['status'] = "running"
    else:
      meeting['status'] = "stopped"
  
  if username.lower() in settings.admins:
    is_admin = True
    users = api.suggest("")
  else:
    is_admin = users = None
  message = request.params.get("message")
  return jinja2_template("main.html", 
                         message=message, 
                         is_admin=is_admin,
                         owners=owners,
                         meeting_list=meeting_list, 
                         username=username,
                         users=users)
  
@route("/login", method=["GET", "POST"])
def login():
  if request.method == "POST":
    username = request.params.get("username")
    password = request.params.get("password")
    ok = api.check(username, password)
    if ok:
      response.set_cookie('username', username, settings.cookie_secret)
      response.set_cookie('password', password, settings.cookie_secret)
      redirect('/start')
    redirect("/login")
  else:
    return jinja2_template("login.html")   
  
  
@route("/logout")
def logout():
  response.delete_cookie("username")
  response.delete_cookie("password")
  redirect("/login")
  

@route("/_create", method=["GET", "POST"])
def create():
  username = request.get_cookie("username", settings.cookie_secret)
  password = request.get_cookie("password", settings.cookie_secret)
  
  ok = api.check(username, password)
  if ok:
    name = request.params.get("name")
    if not api.is_valid(name):
      return "Choose other name"
    
    attendee_users = request.params.get("to_users").split(",")
    attendee_users.remove("")  # remove last comma ","
    moderator_users = [username]
    meeting_id = api.create_meeting(name, attendee_users, moderator_users)
    if meeting_id:
      url = api.join_meeting(username, password, meeting_id)
      redirect(url)
  redirect("/start")

@route("/_join", method="POST")
def join():
  meeting_id = request.params.get("meeting_id")
  username = request.get_cookie("username", settings.cookie_secret)
  password = request.get_cookie("password", settings.cookie_secret)
  ok = api.check(username, password)
  if ok:
    url = api.join_meeting(username, password, meeting_id)
    if url:
      redirect(url)
  redirect("/start?message=permission+denied")
  
@route("/_add_user", method="POST")
def add_user():
  username = request.get_cookie("username", settings.cookie_secret)
  password = request.get_cookie("password", settings.cookie_secret)
  ok = api.check(username, password)
  if ok: 
    username = request.params.get("username")
    password = request.params.get("password")
    api.add_user(username, password)
    redirect("/start?message=ok")
  redirect("/start?message=permission+denied")
  
@route("/_remove_user", method="POST")
def remove_user():
  username = request.get_cookie("username", settings.cookie_secret)
  password = request.get_cookie("password", settings.cookie_secret)
  ok = api.check(username, password)
  if ok: 
    username = request.params.get("username")
    print username
    api.remove_user(username)
  redirect("/start") 

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
      api.change_password(username, new_passwd)
      response.set_cookie('password', new_passwd, settings.cookie_secret)
      redirect("/start")
    redirect("/change_password")
      

@route("/static/:filename#.+#")
def static(filename):
  return static_file(filename, root='static')
  
  

if __name__ == "__main__":
  debug(True)
  run(host="0.0.0.0", port=8888, server="cherrypy")
  
