from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import socket
import json

class ImageSearchServer(ThreadingMixIn,HTTPServer):
	pass

class SearchCase():

	def search_case(self,img_size,img_data):
		c_soc = socket.socket(socket.AF_INET,socket.SOCK_STREAM)         # Create a socket object

		c_soc.connect(("35.200.146.140", 7808))
		print(c_soc.recv(1024))
		c_soc.send(img_size.to_bytes((img_size.bit_length() + 7) // 8,'big'))
		print(c_soc.recv(1024))
		c_soc.send(img_data)

		return c_soc.recv(2048)




class ImageSearchRequestHandler(BaseHTTPRequestHandler):

	def _set_headers(self):
		self.send_response(200)
		

	def do_GET(self):
		self.send_header('Content-type','image/jpeg')
		self.end_headers()
		file_path = "uploads"+self.path
		print(file_path)
		with open(file_path,"rb") as out_f:
			file_data = out_f.read()
		self.wfile.write(file_data)


	def do_POST(self):
		self.send_header('Content-type','text/plain')
		self.end_headers()
		content_len = int(self.headers['Content-Length'])
		data = self.rfile.read(content_len)
		with open("uploads/out.jpg","wb") as img:
			img.write(data)

		print(content_len)

		matches = SearchCase().search_case(content_len,data)
		self.wfile.write("upload done".encode())
		#self.wfile.write(matches)


def run(server_class = ImageSearchServer, handler_class = ImageSearchRequestHandler, port = 80):
	server_address = ('10.142.0.2', port)
	httpd = server_class(server_address, handler_class)
	print('Starting httpd...')
	httpd.serve_forever()

if __name__ == "__main__":
	run()