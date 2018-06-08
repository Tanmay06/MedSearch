from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
import json

class ImageSearchRequestHandler(BaseHTTPRequestHandler):

	def _set_response(self):
		self.send_response(200)
		self.send_header('Content-type','application/json')
		self.end_headers()

	def do_POST(self):
		self._set_response()
		content_len = int(self.headers['Content-Length'])
		data = self.rfile.read(content_len)
		with open("query.jpg","wb") as img:
			img.write(data)

		subprocess.call(['spark-submit','gs://med-search-cluster-script/match.py','query.jpg'])
		
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