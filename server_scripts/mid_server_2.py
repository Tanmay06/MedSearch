from http.server import BaseHTTPRequestHandler,HTTPServer
import requests
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.binary import Binary
from bson.json_util import dumps
from PIL import Image
import io
from urllib.parse import unquote
import json

class DataBaseInteraction():
	
	def get_case_from_db(self,object_id_str):
		mongo_url = "mongodb://userdata:userdata@medsearchcluster-shard-00-00-5lyma.mongodb.net:27017,medsearchcluster-shard-00-01-5lyma.mongodb.net:27017,medsearchcluster-shard-00-02-5lyma.mongodb.net:27017/test?ssl=true&replicaSet=MedSearchCluster-shard-0&authSource=admin"
		
		object_id= ObjectId(object_id_str)
		coll = MongoClient(mongo_url).test_db.cases
		print("Connected to MongoDB Cluster ...")

		case = coll.find_one({"_id":object_id})

		return dumps(case)

	def get_cases_from_ids(self,ids_list):
		ids_list = [ObjectId(x) for x in ids_list]
		
		mongo_url = "mongodb://userdata:userdata@medsearchcluster-shard-00-00-5lyma.mongodb.net:27017,medsearchcluster-shard-00-01-5lyma.mongodb.net:27017,medsearchcluster-shard-00-02-5lyma.mongodb.net:27017/test?ssl=true&replicaSet=MedSearchCluster-shard-0&authSource=admin"
		
		coll = MongoClient(mongo_url).test_db.cases
		print("Connected to MongoDB Cluster ...")
		cases = coll.find({"_id":{"$in":ids_list}},{"_id":1,"data":1})
		
		print("Fetched Case Data ...")	
		return cases

	def get_login(self,login_credentials):
		mongo_url = "mongodb://userdata:userdata@medsearchcluster-shard-00-00-5lyma.mongodb.net:27017,medsearchcluster-shard-00-01-5lyma.mongodb.net:27017,medsearchcluster-shard-00-02-5lyma.mongodb.net:27017/test?ssl=true&replicaSet=MedSearchCluster-shard-0&authSource=admin"
		
		coll = MongoClient(mongo_url).test_db.users
		print("Connected to MongoDB Cluster ...")
		result = coll.find({"$and":[{"uname":login_credentials["uname"]},{"password":login_credentials["password"]}]})

		if result.count() == 1:
			return dumps({"result":"OK"})
		else:
			return dumps({"result":"FAILED"})

	def post_case(self,case_details):
		mongo_url = "mongodb://userdata:userdata@medsearchcluster-shard-00-00-5lyma.mongodb.net:27017,medsearchcluster-shard-00-01-5lyma.mongodb.net:27017,medsearchcluster-shard-00-02-5lyma.mongodb.net:27017/test?ssl=true&replicaSet=MedSearchCluster-shard-0&authSource=admin"
		
		coll = MongoClient(mongo_url).test_db.upcase
		print("Connected to MongoDB Cluster ...")

		case_details["data"] = Binary(case_details["data"].encode())
		case_details["uploader"] = {"uname":case_details["uploader"]}

		res = coll.insert(case_details)
		print(res)
		if isinstance(res,ObjectId):
			return dumps({"result":"OK"})
		else:
			return dumps({"result":"FAILED"})

class DataManupalation():

	def get_image_thumb(self,image_in_bytes):
		img = Image.open(io.BytesIO(image_in_bytes))
		
		base_width = 200
		w_percent = (base_width/float(img.size[0]))
		height = int(float(img.size[1] * float(w_percent)))
		img = img.resize((base_width,height),Image.ANTIALIAS)
		
		bytes_io = io.BytesIO()
		img.save(bytes_io,format="PNG")
		
		return bytes_io.getvalue()

	def set_image_thumbs(self,cases):
		results = []

		for case in cases:
			res = {"_id":str(case["_id"]),"data":DataManupalation.get_image_thumb(self,case["data"])}
			results.append(res)

		return dumps(results)

	def get_search_result(self,img_data):
		url = "http://35.200.146.140:80"
		print("Connected to ",url)
		
		response = requests.post(url,data = img_data)
		result= response.json()
		print(result)

		return result["matches"]


class DataRequestHandler(BaseHTTPRequestHandler):
	
	def _set_response(self):
		self.send_response(200)
		self.send_header('Content-type','application/json')
		self.end_headers()

	def get_params(self):
		params = unquote(self.path)
		params = params[params.find("?")+1::]
		key,value = params.split("=")
		print(key + " " + value)
		return {key:value}

	def do_POST(self):
		self._set_response()
		param = self.get_params()
		content_len = int(self.headers['Content-Length'])
		in_data = self.rfile.read(content_len)

		if param["action"] == "search_case":
			print("Getting result ...")
			result = DataManupalation.get_search_result(self,in_data)
			match_cases = DataBaseInteraction.get_cases_from_ids(self,result)
			match_thumbs = DataManupalation.set_image_thumbs(self,match_cases)
			print("Writing output ...")
			self.wfile.write(match_thumbs.encode())

		elif param["action"] == "post_case":
			print("Posting case ...")
			print(in_data.decode())
			result = DataBaseInteraction.post_case(self,json.loads(in_data.decode()))
			print("Writing output ...")
			self.wfile.write(result.encode())

		elif param["action"] == "login":
			print("Logging in ...")
			result = DataBaseInteraction.get_login(self,json.loads(in_data.decode()))
			print("Writing output ...")
			self.wfile.write(result.encode())

	def do_GET(self):
		self._set_response()
		param = self.get_params()

		case_data = DataBaseInteraction.get_case_from_db(self,param["objectid"])
		print("Writing output ...")
		self.wfile.write(case_data.encode())

def run(server_class = HTTPServer, handler_class = DataRequestHandler, port = 80):
	server_address = ('10.142.0.2', port)
	httpd = server_class(server_address, handler_class)
	print('Starting mid request handler...')
	httpd.serve_forever()
	print("Ready to accept requests ...")

if __name__ == "__main__":
	run()