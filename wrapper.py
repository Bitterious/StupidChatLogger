from threading import Thread
from subprocess import Popen
from time import sleep

keep_running = True
def _run_server():
   proc = Popen(["python", "webserver.py"])
   while True:
       sleep(1)
       if not keep_running:
           proc.terminate()
           break

def _run_client():
   proc = Popen(["python", "client.py"])
   while True:
       sleep(1)
       if not keep_running:
           proc.terminate()
           break

server_th = Thread(target=_run_server)
client_th = Thread(target=_run_client)
server_th.start()
client_th.start()

print("wrapper initialized! :D")
try:
    while True: sleep(.2)
except KeyboardInterrupt:
    keep_running = False

server_th.join()
client_th.join()