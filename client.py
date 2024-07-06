print("starting stupid chatlogger client v2.0")
print("importing libraries")
from os import stat, fstat, path
from re import search
from datetime import datetime
from urllib import parse
from requests import post
from time import sleep
from threading import Thread
from win32gui import FindWindow # type: ignore
from win32process import CreateProcess, IDLE_PRIORITY_CLASS, STARTUPINFO # type: ignore
from tomllib import load
from tomli_w import dump

print("starting script")

COMMIT_AUTH_KEY = ""
TF2_DIR = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Team Fortress 2\\"
TF2_EXECUTABLE = "tf_win64.exe"
TF2_LOG = "tf\\console.log"
REMOTE_ADDRESS = "http://yourserver.here"

try:
	config = load(open("client.toml", "rb"))
	COMMIT_AUTH_KEY = config["commit_key"]
	REMOTE_ADDRESS = config["sv_address"]
	TF2_DIR = config["tf_dir"]
except Exception as e:
	print("invalid client.toml file. regenerating. ERR:{}".format(e))
	if path.exists("client.toml"):
		with open("client.toml.bak", "w") as f:
			prev_f = open("client.toml", "r")
			f.writelines(prev_f.readlines())
			prev_f.close()
			f.close()
	dump({
		"commit_key": "ENTER_SERVER_COMMIT_KEY_HERE",
		"sv_address": "http://localhost:1176",
		"tf_dir": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Team Fortress 2\\"
	}, open("client.toml", "bw"))
	print("regenerated client config please restart the application.")
	quit()

#TODO: OPTIMIZE REGEXES
CHAT_REGEX = ".+[ ]+[:][ ]+.+"
CHAT_USERNAME_EXTRACTOR = ".+?(?= :)"
CHAT_USERNAME_SPECIAL_EXTRACTOR = """((?<=\\(TEAM\\) )|(?<=\\*DEAD\\* |\\*SPEC\\* )).+?(?= :)"""
HOSTNAME_EXTRACTOR = """(?<=hostname: ).+"""
MAPNAME_EXTRACTOR = """(?<=map[ ]{5}: ).+(?= at: )"""
CHAT_CONTENT_EXTRACTOR = "(?<=:  ).+"
IP_EXTRACTOR = "(?<=: ).+"
USER_STATUS_REGEX = """#[ ]+[0-9]+[ ]+\".+\"[ ]+\\[U:1:[0-9]+\\][ ]+[0-9:]+[ ]+[0-9]{0,9}[ ]+[0-9]+ active"""
USERNAME_EXTRACTOR = """\".+\""""
USERID_EXTRACTOR = """\\[U:1:[0-9]+]"""
IP_STATUS_REGEX = "[ ]*udp\\/ip[ ]+[:][ ]+[0-9]{1,3}[.][0-9]{1,3}[.][0-9]{1,3}[.][0-9]{1,3}[:][0-9]{1,6}"
DISCONNECT_REGEX = "Disconnect: .+"
REGISTERED_USERS_LIST = {}
SAVED_HOSTNAME_STR = ""
SAVED_MAPNAME_STR = ""
SAVED_IP_STR = ""

def process_line(l:str):
	global REGISTERED_USERS_LIST
	global SAVED_IP_STR
	global SAVED_MAPNAME_STR
	global SAVED_HOSTNAME_STR
	disconnect = search(DISCONNECT_REGEX,l)
	if disconnect != None:
		REGISTERED_USERS_LIST = {}
		SAVED_IP_STR = ""
		SAVED_MAPNAME_STR = ""
		SAVED_HOSTNAME_STR = ""
		return
	ip = search(IP_STATUS_REGEX,l)
	if ip != None:
		real_ip = search(IP_EXTRACTOR, l)
		if (real_ip != None) and (real_ip.group() != SAVED_IP_STR):
			print("updating current ip to {}".format(real_ip.group()))
			SAVED_IP_STR = real_ip.group()
			if SAVED_HOSTNAME_STR != "":
				post("{}/api/savehost".format(REMOTE_ADDRESS),json={
					"ip": SAVED_IP_STR,
					"nm": SAVED_HOSTNAME_STR
				},headers={
					"Authentication": COMMIT_AUTH_KEY
				})
		return
	hostname = search(HOSTNAME_EXTRACTOR,l)
	if hostname != None:
		if hostname.group() != SAVED_HOSTNAME_STR:
			print("updating current hostname to {}".format(hostname.group()))
			SAVED_HOSTNAME_STR = hostname.group()
		return
	mapname = search(MAPNAME_EXTRACTOR,l)
	if mapname != None:
		if mapname.group() != SAVED_MAPNAME_STR:
			print("updating current map to {}".format(mapname.group()))
			SAVED_MAPNAME_STR = mapname.group()
		return
	chat = search(CHAT_REGEX,l)
	if chat != None:
		chatname = search(CHAT_USERNAME_SPECIAL_EXTRACTOR,chat.group())
		if chatname == None: chatname = search(CHAT_USERNAME_EXTRACTOR,chat.group())
		chattext = search(CHAT_CONTENT_EXTRACTOR,chat.group())
		chattime = datetime.now()
		if (chattext == None): return
		if chatname.group() in REGISTERED_USERS_LIST:
			print("{} said \"{}\" at {} ({})".format(chatname.group(),chattext.group(),chattime.isoformat(),chattime.timestamp()))
			is_team = False
			is_dead = False
			spectator = False
			target_id = REGISTERED_USERS_LIST[chatname.group()].replace("\"","")
			target_data = parse.quote(chattext.group())
			send_time = chattime.timestamp()
			if search("""\\(TEAM\\)""",l) != None: is_team = True
			if search("""\\*DEAD\\*""",l) != None: is_dead = True
			if search("""\\*SPEC\\*""",l) != None: spectator = True
			try:
				post("{}/api/commit".format(REMOTE_ADDRESS),json={
					"id": target_id,
					"tx": target_data,
					"ti": send_time,
					"sv": SAVED_IP_STR,
					"dd": is_dead,
					"tm": is_team,
					"sp": spectator,
					"mp": SAVED_MAPNAME_STR
				},headers={
					"Authentication": COMMIT_AUTH_KEY
				})
			except Exception:
				print("Cant post chat. {}".format(Exception))
		return
	user = search(USER_STATUS_REGEX,l)
	if user != None:
		username = search(USERNAME_EXTRACTOR,user.group())
		userid = search(USERID_EXTRACTOR,user.group())
		if not (username.group().replace("\"","") in REGISTERED_USERS_LIST):
			print("saving {}'s id to {}".format(username.group(),userid.group()))
			REGISTERED_USERS_LIST[username.group().replace("\"","")] = userid.group()
		return


def follow(name):
	current = open(name, "r", encoding="utf-8", errors="replace")
	curino = fstat(current.fileno()).st_ino
	while True:
		while True:
			try:
				line = current.readline()
				if not line:
					break
				yield line
			except UnicodeDecodeError:
				print("CANT DECODE LINE")
		try:
			if stat(name).st_ino != curino:
				new = open(name, "r")
				current.close()
				current = new
				curino = fstat(current.fileno()).st_ino
				continue
		except IOError:
			pass
		sleep(1)

stop_thread = False
already_warned = False
def _tf2_hijack_thread():
	global already_warned
	while not stop_thread:
		sleep(3)
		if stop_thread: return
		if not FindWindow("Valve001", None):
			if not already_warned: print("TF2 is not running."); already_warned = True
			continue
		command = "{} -game tf -hijack +clear +status".format(TF2_DIR+TF2_EXECUTABLE)
		already_warned = False
		try:
			CreateProcess(None,command,None,None,False,IDLE_PRIORITY_CLASS,None,TF2_DIR,STARTUPINFO())
		except Exception as e:
			print("failed to send command to tf2_64.exe: {}".format(e))

print("starting hijack thread...")
tf2_hijack_thread = Thread(target=_tf2_hijack_thread)
tf2_hijack_thread.start()
print("started hijack thread")
print("remote server is {}".format(REMOTE_ADDRESS))
print("press ctrl+c to stop")

stopped = False
def stop():
	stopped = True

tf2_log_path = TF2_DIR+TF2_LOG
if path.exists(tf2_log_path):
	with open(tf2_log_path, "w") as f:
		f.write("")
		f.flush()
		f.close()
try:
	for l in follow(tf2_log_path):
		if __name__ != '__main__' & stopped:
			print("stopping client")
			break
		process_line(l)
except Exception as e:
	print("exception occurred: {}".format(e))
print("stopping hijack thread")
stop_thread = True
tf2_hijack_thread.join()
print("script end")