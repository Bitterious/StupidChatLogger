# Stupid Chatlogger  
#### very dumb chatlogger for tf2  
*might work for other source games didnt test it*  
## what can it do?  
### pros  
- can capture (TEAM) and \*DEAD\* prefixes  
- saves using userids so changing account name or link doesnt delete you from the database  
- has bunch of search options (map,server name,username etc.)  
- takes virtually no space (100kb ~= 1000 messages)  
- saves usernames incase profiles get removed (indicated by ⚠ next to username)  
- doesnt require tf2 side configuration  
- doesnt inject code to tf2 so not VAC bannable  
### cons  
- written by a dumbshit  
- sometimes not stable  
- uses an obscure fast ass fuck framework  
- first loads are slow  
- bad ui (i dont know css)  
## drop examples dumbass  
try my own personal one [here](https://tf2logs.bittless.xyz)
## how to install tho?  
1. clone or download this repository  
2. install requirements  

`` on linux:``  
!! can only run the webserver!!
```bash
pip install -r requirements-webserver.txt
pip install -r requirements-webserver-posix.txt
```  
`` on windows:``  
```bash
pip install -r requirements-client.txt
pip install -r requirements-webserver.txt
pip install -r requirements-webserver-win32.txt
```  
and thats it  
## running this godawful code  
!!!!! ONLY WINDOWS CAN RUN THE CLIENT I AM TOO LAZY TO MAKE IT ON LINUX !!!!!  
``python wrapper.py`` (windows only) runs both client and webserver  
``python client.py`` (windows only) runs just the client (preferred when you already have a server running)  
``python webserver.py`` runs just the webserver. webserver holds all the data so its required for client to function  