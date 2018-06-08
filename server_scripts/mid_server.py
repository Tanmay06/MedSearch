"""This is a Python server which acts as abstraction over spark cluster and mongoDB cluster, and interface for end user. Currently it is single threaded and therefore serves single request at a time. It serves both POST and GET requests. The POST method expects action parameter in url which tells the program which action should be performed. Currently it supports: 1.search - searching for case 2.post - posting case 3.login - loggin in user The GET method serves just purpose of fetching the requested case details. For other details refer README.md"""

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

#DataBaseInteraction class handles all the interaction with the mongoDB database like posting data, fetching data or using user data to login. 
class DataBaseInteraction():
	
	#MongoDB cluster url for connection 
	mongo_url = "mongodb://<Username>:<Password>@<MongoDB cluster url depending on your pymongo driver version. Refer pymongo and mongoDB docs for more information>"
	
	#This method is used to fetch details of a case from the database. It takes object_id(string) of the case as argument and returns JSON string containing details of the case.  
	def get_case_from_db(self,object_id_str):
		
		object_id= ObjectId(object_id_str)
		coll = MongoClient(mongo_url).test_db.cases
		print("Connected to MongoDB Cluster ...")

		case = coll.find_one({"_id":object_id})

		return dumps(case)
	
	#This method is used to fetch images of cases from the database. It takes a list of object_id(string[]) of the cases as argument and returns a pymongo.cursor object which can be used to iterate over JSON doc of each case containing object_id and data of the case.
	def get_cases_from_ids(self,ids_list):
		ids_list = [ObjectId(x) for x in ids_list]
		
		coll = MongoClient(mongo_url).test_db.cases
		print("Connected to MongoDB Cluster ...")
		cases = coll.find({"_id":{"$in":ids_list}},{"_id":1,"data":1})
		
		print("Fetched Case Data ...")	
		return cases
	
	#This method is used to provide login for users. It takes a dict containing username(uname) and password(password) as argument and returns a JSON string which tells the status of login attempt.
	def get_login(self,login_credentials):
		
		coll = MongoClient(mongo_url).test_db.users
		print("Connected to MongoDB Cluster ...")
		result = coll.find({"$and":[{"uname":login_credentials["uname"]},{"password":login_credentials["password"]}]})

		if result.count() == 1:
			return dumps({"result":"OK"})
		else:
			return dumps({"result":"FAILED"})
	
	#This method is used to post a case in database. It takes dict containing case details as argument and returns JSON string containing status of posting attempt.
	def post_case(self,case_details):
		
		coll = MongoClient(mongo_url).test_db.upcase
		print("Connected to MongoDB Cluster ...")

		case_details["data"] = Binary(case_details["data"].encode())
		case_details["uploader"] = {"uname":case_details["uploader"]}

		res = coll.insert(case_details)
		print(res)
		
		#coll.insert return a bson.objectid if inserting in database is successful. This fact is used to check whether the case is successfully posted in the database. 
		if isinstance(res,ObjectId):
			return dumps({"result":"OK"})
		else:
			return dumps({"result":"FAILED"})

#DataManipulation handles all data manipulation jobs required at runtime and it even handles communication with Spark cluster for search case jobs.
class DataManupalation():

	#get_image_thub is used to get a thumbnail version of actual image provide in bytes. It takes a full size bytes of image as argument and returns a 200x(calculated height) PNG bytes of the image.
	def get_image_thumb(self,image_in_bytes):
		img = Image.open(io.BytesIO(image_in_bytes))
		
		base_width = 200
		w_percent = (base_width/float(img.size[0]))
		height = int(float(img.size[1] * float(w_percent)))
		img = img.resize((base_width,height),Image.ANTIALIAS)
		
		bytes_io = io.BytesIO()
		img.save(bytes_io,format="PNG")
		
		return bytes_io.getvalue()
	
	#This method is used to get thumbnails of a list of cases. It takes a pymongo.cursor as argument and returns a JSON string with object_id and thumbnailed version of original image of each case.
	def set_image_thumbs(self,cases):
		results = []

		for case in cases:
			res = {"_id":str(case["_id"]),"data":DataManupalation.get_image_thumb(self,case["data"])}
			results.append(res)

		return dumps(results)
	
	#This method is used to send search request to the Spark cluster. It takes bytes data of image as argument and returns a list of object_ids of the cases matching the queried image.
	def get_search_result(self,img_data):
		url = "<Spark cluster's master node's ,which is handling http requests, url>"
		print("Connected to ",url)
		
		#sending post request to the spark cluster.
		response = requests.post(url,data = img_data)
		result= response.json()
		print(result)

		return result["matches"]

#DataRequestHandler is a HTTP request handler class. It extends BaseHTTPRequestHandler and provides method to serve POST and GET requests.
class DataRequestHandler(BaseHTTPRequestHandler):
	
	#This method is used to set headers of the response generated for the request.
	def _set_response(self):
		self.send_response(200)
		self.send_header('Content-type','application/json')
		self.end_headers()

	#This method is used to fetch params passed in the url with the request. It return a dict of params and its' values.
	def get_params(self):
		params = unquote(self.path)
		params = params[params.find("?")+1::]
		key,value = params.split("=")
		print(key + " " + value)
		return {key:value}

	#do_POST serves the POST request and responds with appropriate response.
	def do_POST(self):
		self._set_response()
		param = self.get_params()
		content_len = int(self.headers['Content-Length'])
		in_data = self.rfile.read(content_len)
		
		#According to the request the program is branched to various cases.
		
		#Serving search_case, uses image data in the request and sends it to spark cluster for searching.
		if param["action"] == "search_case":
			print("Getting result ...")
			result = DataManupalation.get_search_result(self,in_data)#sending image to spark cluster
			match_cases = DataBaseInteraction.get_cases_from_ids(self,result)#fetching cases from mongodb
			match_thumbs = DataManupalation.set_image_thumbs(self,match_cases)#converting case image tpo thumbnails
			print("Writing output ...")
			#sending the response
			self.wfile.write(match_thumbs.encode())

		#Serving post_case, uses case data in the request and inserts it in the mongodb
		elif param["action"] == "post_case":
			print("Posting case ...")
			print(in_data.decode())
			
			result = DataBaseInteraction.post_case(self,json.loads(in_data.decode()))#the data received is JSON encoded string in bytes, it converted to JSON string and uploaded to mongodb 
			print("Writing output ...")
			self.wfile.write(result.encode())
		
		#Serving login, uses the username and password in request data to login
		elif param["action"] == "login":
			print("Logging in ...")
			result = DataBaseInteraction.get_login(self,json.loads(in_data.decode()))
			print("Writing output ...")
			self.wfile.write(result.encode())
	
	#do_GET serves GET requests to server
	def do_GET(self):
		self._set_response()
		param = self.get_params()

		case_data = DataBaseInteraction.get_case_from_db(self,param["objectid"])#sends object_id for fetching case details 
		print("Writing output ...")
		self.wfile.write(case_data.encode())

#This methos is used to initialize and start the server. 
def run(server_class = HTTPServer, handler_class = DataRequestHandler, port = 80):
	server_address = ('10.142.0.2', port)
	httpd = server_class(server_address, handler_class)
	print('Starting mid request handler...')
	httpd.serve_forever()
	print("Ready to accept requests ...")

if __name__ == "__main__":
	run()
