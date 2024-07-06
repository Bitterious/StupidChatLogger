from urllib.parse import quote, unquote, urlencode
from bottle import route, run, template, post, request, \
response, static_file, redirect, abort, error, TEMPLATE_PATH
import gevent.monkey
from requests import get as http_get
from json import loads as j_loads
from math import ceil, floor
from os import path, name
from psutil import cpu_percent, cpu_freq, getloadavg, virtual_memory
from sys import getsizeof
from tomllib import load
from tomli_w import dump
from secrets import token_urlsafe
from re import search
from datetime import datetime

import dbtool
import steamid_tools
from time_ago import time_ago

TEMPLATE_PATH.insert(0, 'templates')

SERVER_SECRET = ""
COMMIT_API_KEY = ""
STEAM_API_KEY = ""
OWNER_STEAM_ID = ""
SERVER_PORT = 1176
STEAM_GET_USER_DATA = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={}&steamids={}"

try:
	config = load(open("webserver.toml", "rb"))
	SERVER_SECRET = config["sv_secret"]
	COMMIT_API_KEY = config["client_key"]
	STEAM_API_KEY = config["steam_api_key"]
	SERVER_PORT = config["sv_port"]
except Exception as e:
	print("Invalid webserver.toml file. regenerating. ERR:{}".format(e))
	if path.exists("webserver.toml"):
		with open("webserver.toml.bak", "w") as f:
			prev_f = open("webserver.toml", "r")
			f.writelines(prev_f.readlines())
			prev_f.close()
			f.close()
	dump({
		"sv_secret": token_urlsafe(64),
		"client_key": "bittworks-"+token_urlsafe(256),
		"steam_api_key": "DUMMY",
		"owner": "your-id-here",
		"sv_port": 1176,
	}, open("webserver.toml", "bw"))
	print("regenerated webserver config please restart the application.")
	quit()


CACHED_USERS = {}

@post('/api/commit')
def commit_chat():
	global CACHED_USERS
	ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
	if request.headers["Authentication"] != COMMIT_API_KEY:
		return abort(401, "Auth Error")
	id = request.json["id"]
	tx = unquote(request.json["tx"])
	ti = request.json["ti"]
	sv = request.json["sv"]
	dd = request.json["dd"]
	tm = request.json["tm"]
	sp = request.json["sp"]
	mp = request.json["mp"]
	dbtool.execute_push_query(dbtool.INSERT_ROW,(id,tx,ti,sv,dd,tm,sp,mp))
	commid = steamid_tools.usteamid_to_commid(id)
	if commid in CACHED_USERS:
		user_data = CACHED_USERS[commid]
		username = user_data["username"]
		dbtool.execute_push_query(dbtool.INSERT_USERNAME_ROW,(id,username))
	else:
		resp = http_get(STEAM_GET_USER_DATA.format(STEAM_API_KEY, commid))
		user = resp.json()["response"]["players"][0]
		username = user["personaname"]
		userurl = user["profileurl"]
		avatarurl = user["avatarmedium"]
		fullavatarurl = user["avatarfull"]
		dbtool.execute_push_query(dbtool.INSERT_USERNAME_ROW,(id,username))
		CACHED_USERS[commid] = {
			"username": username,
			"userurl": userurl,
			"avatarurl": avatarurl,
			"bigavatarurl": fullavatarurl
		}
	print("[{}]: Commiting chat data push. {} => {} @ {}".format(ip,id,tx,ti))

@post('/api/savehost')
def commit_host():
	ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
	if request.headers["Authentication"] != COMMIT_API_KEY:
		return abort(401, "Auth Error")
	svid = request.json["ip"]
	hostname = request.json["nm"]
	dbtool.execute_push_query(dbtool.INSERT_SERVERNAME_ROW,(svid,hostname))
	print("[{}]: Commiting server data push. {} => {}".format(ip,svid,hostname))


@post('/query/search')
def query_search():
	ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
	reqtype = request.forms.get("type")
	misc = request.forms.get("namebox")
	print("[{}]: Query request. {} ?{}".format(ip,reqtype, misc))
	match reqtype:
		case "name":
			return redirect("/n/{}/1".format(quote(misc)))
		case "user":
			return redirect("/u/{}/1".format(misc))
		case "ip":
			return redirect("/s/{}/1".format(quote(misc)))
		case "servers":
			return redirect("/h/{}/1".format(quote(misc)))
		case "contains":
			return redirect("/c/{}/1".format(quote(misc)))
		case "map":
			return redirect("/m/{}/1".format(quote(misc)))
		case _:
			return abort(404,"Wrong/Missing query data.")

@route('/static/<file>')
def static_access(file):
	path = unquote(file)
	ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
	print("[{}]: File request: {}".format(ip,path))
	return static_file(path, root='static')

@route('/map/<file>')
def map_image_access(file):
	path = unquote(file)
	ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
	print("[{}]: Map image request: {}".format(ip,path))
	if path.exists("./static/tf2maps/%s.jpeg" % path):
		return static_file(path+".jpeg", root='static/tf2maps')
	else:
		return static_file("unknown.jpeg", root='static/tf2maps')

def parse_commits(to_parse):
	global CACHED_USERS
	commits = []
	for data in to_parse:
		userid = data[1]
		communityid = steamid_tools.usteamid_to_commid(userid)
		parsed_time = time_ago(int(data[3]))
		time_iso = datetime.fromtimestamp(data[3]).isoformat()
		server_ip = data[4]
		server_tag = server_ip
		hostname_query = dbtool.execute_get_query(dbtool.GET_HOSTNAME,(server_ip,))
		if len(hostname_query) > 0:
			server_tag = hostname_query[0][0]
		is_dead = data[5]
		is_team = data[6]
		spectator = data[7]
		if communityid in CACHED_USERS:
			cache = CACHED_USERS[communityid]
			commits.append({
				"index": data[0],
				"name": cache["username"],
				"url": cache["userurl"],
				"avatar": cache["avatarurl"],
				"content": data[2],
				"time": parsed_time,
				"server": server_tag,
				"is_dead": is_dead,
				"is_team": is_team,
				"spectator": spectator,
				"user_id": communityid,
				"map": data[8],
				"time_og": time_iso,
				"server_ip": server_ip
			})
			continue
		response = http_get(STEAM_GET_USER_DATA.format(STEAM_API_KEY,communityid))
		if (response == None) or (response.status_code != 200): continue
		parsed = j_loads(response.content)
		usercon = parsed["response"]["players"]
		username = "[removed from steam]"
		userurl = "https://steamcommunity.com/profiles/{}.".format(communityid)
		avatarurl = "/static/missing_pfp.jpg"
		fullavatarurl = "/static/missing_pfp.jpg"
		if len(usercon) > 0:
			user = usercon[0]
			username = user["personaname"]
			userurl = user["profileurl"]
			avatarurl = user["avatarmedium"]
			fullavatarurl = user["avatarfull"]
			CACHED_USERS[communityid] = {
				"username": username,
				"userurl": userurl,
				"avatarurl": avatarurl,
				"bigavatarurl": fullavatarurl
			}
		else:
			savedusername = dbtool.execute_get_query(dbtool.GET_SAVED_USERNAME_BY_ID,(userid,))[0][1]
			username = "{} ⚠".format(savedusername)
		commits.append({
			"index": data[0],
			"name": username,
			"url": userurl,
			"avatar": avatarurl,
			"content": data[2],
			"time": parsed_time,
			"server": server_tag,
			"is_dead": is_dead,
			"is_team": is_team,
			"spectator": spectator,
			"user_id": communityid,
			"map": data[8],
			"time_og": time_iso,
			"server_ip": server_ip
		})
	return commits

@route('/u/<id>')
@route('/u/<id>/<page>')
def get_by_user(id:str,page=1):
	ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
	print("[{}]: Querying user {} page {}.".format(ip,id,page))
	global CACHED_USERS
	if not id.isdigit():
		return abort(400, "Invalid UserID")
	user_id = steamid_tools.commid_to_usteamid(id)
	user_commits = dbtool.execute_get_query(dbtool.GET_USER_X_ROWS,(user_id,20,(int(page)-1)*20))
	commits = parse_commits(user_commits)
	commit_count = dbtool.execute_get_query(dbtool.GET_USER_TOTAL_ROWS,(user_id,))[0][0]
	total_pages = ceil(commit_count / 20)
	userdata = {
		"username": "SERVER SIDE EXCEPTION [CACHE_FAIL]",
		"userurl": "",
		"avatarurl": "/static/missing_pfp.jpg",
		"bigavatarurl": "/static/missing_pfp.jpg"
	}
	if int(id) in CACHED_USERS: userdata = CACHED_USERS[int(id)]
	return template("templates/byuser.html",commits=commits,page=int(page),totalpages=total_pages,userdata=userdata,uid=id)

@route('/n/<name>')
@route('/n/<name>/<page>')
def get_by_name(name:str,page=1):
	ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
	print("[{}]: Querying name {} page {}.".format(ip,name,page))
	global CACHED_USERS
	r_name = unquote(name)
	per_name = "%{}%".format(r_name)
	users = dbtool.execute_get_query(dbtool.GET_SIMILAR_USERNAMES,(per_name,20,(int(page)-1)*20))
	user_count = dbtool.execute_get_query(dbtool.GET_TOTAL_SIMILAR_USERNAMES,(per_name,))[0][0]
	total_pages = ceil(user_count / 20)
	commits = []
	for user in users:
		uid = user[0]
		commid = steamid_tools.usteamid_to_commid(uid)
		if commid in CACHED_USERS:
			cache = CACHED_USERS[commid]
			commits.append({
				"name": cache["username"],
				"avatar": cache["avatarurl"],
				"user_id": commid
			})
			continue
		response = http_get(STEAM_GET_USER_DATA.format(STEAM_API_KEY,commid))
		if (response == None) or (response.status_code != 200): continue
		parsed = j_loads(response.content)
		usercon = parsed["response"]["players"]
		username = "[removed from steam]"
		userurl = "https://steamcommunity.com/profiles/{}.".format(commid)
		avatarurl = "/static/missing_pfp.jpg"
		fullavatarurl = "/static/missing_pfp.jpg"
		if len(usercon) > 0:
			user = usercon[0]
			username = user["personaname"]
			userurl = user["profileurl"]
			avatarurl = user["avatarmedium"]
			fullavatarurl = user["avatarfull"]
			CACHED_USERS[commid] = {
				"username": username,
				"userurl": userurl,
				"avatarurl": avatarurl,
				"bigavatarurl": fullavatarurl
			}
		else:
			username = "{} ⚠".format(user[1])
		commits.append({
			"name": username,
			"avatar": avatarurl,
			"user_id": commid
		})
	return template("templates/byname.html",commits=commits,page=int(page),totalpages=total_pages,name=name,p_name=r_name)

@route('/s/<ip>')
@route('/s/<ip>/<page>')
def get_by_server(ip,page=1):
	userip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
	print("[{}]: Querying server {} page {}.".format(userip,ip,page))
	real_ip = unquote(ip)
	valid_ip = search("""(?<![0-9])[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}:[0-9]{1,6}""", real_ip)
	if not valid_ip:
		return abort(400,"Invalid IP")
	server_commits = dbtool.execute_get_query(dbtool.GET_SERVER_X_ROWS,(ip,20,(int(page)-1)*20))
	commits = parse_commits(server_commits)
	commit_count = dbtool.execute_get_query(dbtool.GET_SERVER_TOTAL_ROWS,(real_ip,))[0][0]
	total_pages = ceil(commit_count / 20)
	return template("templates/byserver.html",commits=commits,page=int(page),totalpages=total_pages,ip=real_ip,oip=ip)

@route('/h/<hostname>')
@route('/h/<hostname>/<page>')
def get_by_hostname(hostname,page=1):
	userip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
	print("[{}]: Querying hostname {} page {}.".format(userip,hostname,page))
	absolute_hostname = unquote(hostname)
	servers = dbtool.execute_get_query(dbtool.GET_IPS_BY_HOSTNAME,(absolute_hostname,page,(int(page)-1)*20))
	commits = []
	for server in servers:
		commits.append({
			"ip": server[0],
			"hostname": server[1],
		})
	commit_count = dbtool.execute_get_query(dbtool.GET_COUNT_OF_SIMILAR_HOSTNAME,(absolute_hostname,))[0][0]
	total_pages = ceil(commit_count / 20)
	return template("templates/byhostname.html",commits=commits,page=int(page),totalpages=total_pages,name=absolute_hostname,oname=hostname)

@route('/c/<txt>')
@route('/c/<txt>/<page>')
def get_by_similar(txt,page=1):
	ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
	print("[{}]: Querying chat {} page {}.".format(ip,txt,page))
	real_txt = unquote(txt)
	per_txt = "%{}%".format(real_txt)
	similar_commits = dbtool.execute_get_query(dbtool.GET_SIMILAR_X_ROWS,(per_txt,20,(int(page)-1)*20))
	commits = parse_commits(similar_commits)
	commit_count = dbtool.execute_get_query(dbtool.GET_SIMILAR_TOTAL_ROWS,(per_txt,))[0][0]
	total_pages = ceil(commit_count / 20)
	return template("templates/bychat.html",commits=commits,page=int(page),totalpages=total_pages,txt=real_txt,otxt=txt)

@route('/m/<map>')
@route('/m/<map>/<page>')
def get_by_map(map,page=1):
	ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
	print("[{}]: Querying maps {} page {}.".format(ip,map,page))
	map_name = unquote(map)
	similar_commits = dbtool.execute_get_query(dbtool.GET_ONMAP_X_ROWS,(map_name,20,(int(page)-1)*20))
	commits = parse_commits(similar_commits)
	commit_count = dbtool.execute_get_query(dbtool.GET_ONMAP_TOTAL_ROWS,(map_name,))[0][0]
	total_pages = ceil(commit_count / 20)
	return template("templates/bymap.html",commits=commits,page=int(page),totalpages=total_pages,map=map_name,omap=map)

@route('/')
@route('/index')
@route('/index/<page>')
def index(page=1):
	ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.environ.get('REMOTE_ADDR')
	print("[{}]: Preparing index page {}.".format(ip, page))
	last_commits = dbtool.execute_get_query(dbtool.GET_NEWEST_X_ROWS,(20,(int(page)-1)*20))
	total_commits = dbtool.execute_get_query(dbtool.GET_TOTAL_ROWS)[0][0]
	commits = parse_commits(last_commits)
	total_pages = ceil(total_commits / 20)
	return template("templates/index.html",commits=commits,page=int(page),totalpages=total_pages)

STEAM_OPENID_URL = 'https://steamcommunity.com/openid/login'
@route('/steam_authentication')
def _steam_authenticate():
	if request.get_cookie("steam_id", secret=SERVER_SECRET) != None: return redirect('/')
	params = {
		'openid.ns': "http://specs.openid.net/auth/2.0",
		'openid.identity': "http://specs.openid.net/auth/2.0/identifier_select",
		'openid.claimed_id': "http://specs.openid.net/auth/2.0/identifier_select",
		'openid.mode': 'checkid_setup',
		'openid.return_to': 'https://tf2logs.bittless.xyz/steam_authorize',
		'openid.realm': 'https://tf2logs.bittless.xyz/'
	}
	query = urlencode(params)
	url = "{}?{}".format(STEAM_OPENID_URL,query)
	return redirect(url)

@route('/steam_authorize')
def _steam_authorize():
	idlink = request.query["openid.identity"]
	id = search("(?<=id\\/)[0-9]+", idlink).group()
	response.set_cookie("steam_id", id, secret=SERVER_SECRET)
	return redirect('/')

mb_conversion_rate = 0.00000095367432
@route('/dev/index')
@route('/dev/')
@route('/dev')
def _status_page():
	user = request.get_cookie("steam_id", secret=SERVER_SECRET)
	if not user: return redirect('/')
	db_size = path.getsize("data.db")
	db_rows = dbtool.execute_get_query(dbtool.GET_ROW_COUNT)[0][0]
	cpu_usage = cpu_percent(.3)
	cpu_speed = cpu_freq()
	load_avg = getloadavg()
	vram = virtual_memory()
	free_ram = floor(vram.available * 100 / vram.total)
	used_ram = vram.percent
	total_ram_mb = floor(vram.total * mb_conversion_rate)
	used_ram_mb = floor(vram.used * mb_conversion_rate)
	cache_size = len(CACHED_USERS)
	cache_bytes = getsizeof(CACHED_USERS)
	return template("templates/_index.html",user_id=user,db_bytes=db_size,cpu_percent=cpu_usage,\
				 free_ram=free_ram,used_ram=used_ram,load_avg=load_avg,cpu_ghz=cpu_speed[0],\
					used_ram_mb=used_ram_mb,total_ram_mb=total_ram_mb,db_rows=db_rows,\
						cache_size=cache_size,cache_bytes=cache_bytes)

@error(400)
@error(401)
@error(404)
@error(405)
@error(500)
def error_page(error):
	return template("templates/error404.html",error=error)

@route('/changelogs')
def changelogs():
	return template("templates/changelogs.html")

if name == "posix": # unix and unixlike
	run(host="0.0.0.0", port=SERVER_PORT, server="bjoern")
else: # windows
	import gevent
	gevent.monkey.patch_all(ssl=False)
	run(host="0.0.0.0", port=SERVER_PORT, server="gevent")