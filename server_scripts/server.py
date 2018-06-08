import socket
import subprocess

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM,0)         # Create a socket object
host = socket.gethostname() # Get local machine name
port = 7808          # Reserve a port for your service.
s.bind(("10.160.0.4", port))        # Bind to the port

s.listen(5)                 # Now wait for client connection.

while True:
   c, addr = s.accept()     # Establish connection with client.
   print('Got connection from', addr)
   c.send(bytes('Thank you for connecting send image size ..','utf-8'))
   img_size = int.from_bytes(c.recv(1024),'big')
   print(img_size)
   c.send(bytes('Thank you for connecting send image ..','utf-8'))
   img_data = c.recv(img_size)

   with open("query.jpg","wb") as q_file:
   	q_file.write(img_data)


   subprocess.call(['spark-submit','gs://med-search-cluster-script/match.py','query.jpg'])

   with open("out.json","r") as out_f:
   	data = out_f.read()

   c.send(bytes(data,'utf-8'))
   
   c.close()                # Close the connection