"""This is python server script which is deployed on master node of the spark cluster. It serves the POST request to handle image search jobs. It expects a image file in the request, which used as queried image for the spark job. The spark job is called a subprocess of the program."""

from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
import json

#ImageSearchRequestHandler handles HTTP POST request and calls the spark job
class ImageSearchRequestHandler(BaseHTTPRequestHandler):

	#
	def _set_response(self):
		self.send_response(200)
		self.send_header('Content-type','application/json')
		self.end_headers()

	#do_POST handles the post request for the server
	def do_POST(self):
		self._set_response()
		content_len = int(self.headers['Content-Length'])
		data = self.rfile.read(content_len)
		
		#saving image to local storage
		with open("query.jpg","wb") as img:
			img.write(data)
		
		#starting the spark job the spark outputs to out.json on local storage
		subprocess.call(['spark-submit','<dir location>/match.py','query.jpg'])
		
		#reading the output from spark job and sending it in response.
		with open("out.json","rb") as out_f:
			data = out_f.read()

		print("Writing response ..")
		self.wfile.write(data)
		print("Response sent..")


def run(server_class = HTTPServer, handler_class = ImageSearchRequestHandler, port = 80):
	server_address = ('10.160.0.4', port)
	httpd = server_class(server_address, handler_class)
	print('Starting httpd...')
	httpd.serve_forever()

if __name__ == "__main__":
	run()
