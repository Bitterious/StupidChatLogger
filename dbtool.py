import sqlite3
CREATE_TABLE = """CREATE TABLE IF NOT EXISTS chats (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user TEXT,
  data TEXT,
  said_at REAL,
  server_ip TEXT,
  is_dead BOOLEAN,
  is_team BOOLEAN,
  spectating BOOLEAN,
  map_name TEXT
)"""
CREATE_USERNAME_TABLE = """CREATE TABLE IF NOT EXISTS usernameids (
	id TEXT PRIMARY KEY,
	username TEXT
)"""
CREATE_SERVERNAME_TABLE = """CREATE TABLE IF NOT EXISTS servernames (
	ip TEXT PRIMARY KEY,
	hostname TEXT
)"""
INSERT_ROW = """INSERT INTO chats (user, data, said_at, server_ip, is_dead, is_team, spectating, map_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
INSERT_USERNAME_ROW = """INSERT OR REPLACE INTO usernameids (id, username) VALUES (?, ?)"""
INSERT_SERVERNAME_ROW = """INSERT OR REPLACE INTO servernames (ip, hostname) VALUES (?, ?)"""
GET_HOSTNAME = """SELECT hostname FROM servernames WHERE ip = ?"""
GET_IPS_BY_HOSTNAME = """SELECT * FROM servernames WHERE hostname LIKE ? LIMIT ? OFFSET ?"""
GET_COUNT_OF_SIMILAR_HOSTNAME = """SELECT COUNT(*) FROM servernames WHERE hostname LIKE ?"""
GET_SIMILAR_USERNAMES = """SELECT * FROM usernameids WHERE username LIKE ? LIMIT ? OFFSET ?"""
GET_TOTAL_SIMILAR_USERNAMES = """SELECT COUNT(*) FROM usernameids WHERE username LIKE ?"""
GET_NEWEST_X_ROWS = """SELECT * FROM chats ORDER BY said_at DESC LIMIT ? OFFSET ?"""
GET_TOTAL_ROWS = """SELECT COUNT(*) FROM chats"""
GET_USER_X_ROWS = """SELECT * FROM chats WHERE user = ? ORDER BY said_at DESC LIMIT ? OFFSET ?"""
GET_SERVER_X_ROWS = """SELECT * FROM chats WHERE server_ip = ? ORDER BY said_at DESC LIMIT ? OFFSET ?"""
GET_USER_TOTAL_ROWS = """SELECT COUNT(*) FROM chats WHERE user = ?"""
GET_SERVER_TOTAL_ROWS = """SELECT COUNT(*) FROM chats WHERE server_ip = ?"""
GET_SIMILAR_X_ROWS = """SELECT * FROM chats WHERE data LIKE ? ORDER BY said_at DESC LIMIT ? OFFSET ?"""
GET_SIMILAR_TOTAL_ROWS = """SELECT COUNT(*) FROM chats WHERE data LIKE ?"""
GET_ONMAP_X_ROWS = """SELECT * FROM chats WHERE map_name = ? ORDER BY said_at DESC LIMIT ? OFFSET ?"""
GET_ONMAP_TOTAL_ROWS = """SELECT COUNT(*) FROM chats WHERE map_name = ?"""
GET_ROW_COUNT = """SELECT COUNT(*) FROM chats"""
GET_SAVED_USERNAME_BY_ID = """SELECT * FROM usernameids WHERE id = ?"""

SAVED_DB = sqlite3.connect("data.db")
DB_CURSOR = SAVED_DB.cursor()
DB_CURSOR.execute(CREATE_TABLE)
DB_CURSOR.execute(CREATE_USERNAME_TABLE)
DB_CURSOR.execute(CREATE_SERVERNAME_TABLE)
print("database connected")

def execute_get_query(query,params = ()):
	DB_CURSOR.execute(query,params)
	data = DB_CURSOR.fetchall()
	return data

def execute_push_query(query,params = ()):
	DB_CURSOR.execute(query,params)
	SAVED_DB.commit()
