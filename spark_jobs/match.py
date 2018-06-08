import cv2
from pyspark import SparkContext
from pyspark.sql import SparkSession
import numpy as np
import sys
from urllib.request import Request,urlopen
import json

#Initialising spark context
spark_c = SparkContext(appName="Get Images")

#initializing Spark Session
spark_s = SparkSession(spark_c)

#function to match features of file 
def match_features(main_img,file):
	#initialising matcher object
	bf_matcher = cv2.BFMatcher_create()	

	#converting bytearray of images descriptors to ndarray
	test_desc = np.frombuffer(file[1],dtype='float32').reshape(file[2])

	matches = bf_matcher.knnMatch(main_img,test_desc, k = 2)
	good_matches = []
	for m,n in matches:
		if m.distance < 0.75* n.distance:
			good_matches.append([m])

	if len(good_matches) >= 10:
		return (file[0],len(good_matches))

def get_img(img_url):
	"""url_request = Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
	in_img = urlopen(url_request).read()
	with open("try.jpg","wb") as df:
		df.write(in_img)
		
	img = cv2.imread("try.jpg",0)
	return img"""
	return cv2.imread(img_url,0)

#initialising sift object and test image features
sift = cv2.xfeatures2d.SIFT_create(200,5)
kps,desc = sift.detectAndCompute(get_img(sys.argv[1]),None)

#initialising images data RDD
image_data = spark_s.read.parquet("hdfs://med-search-m/user/tanmayvakare/image_data.parquet")

#matching features 
matches = image_data.rdd.map(lambda x: match_features(desc,x)).filter(lambda x: x is not None).collect()

print(matches)

match_ids = []

for x in matches:
	match_ids.append(x[0].oid)

print(match_ids)

with open("out.json","w") as out_f:
	out_f.write(json.dumps({"matches":match_ids}))

print({"matches":match_ids})

 