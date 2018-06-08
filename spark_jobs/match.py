"""This pyspark job matches the features of queried image to that of images in the database. The features of the images in database is obtained through parqueet file, which is generated by load_job.py, stored in HDFS. The program uses bruteforce KNN matching to match features. It stores the result in out.json file which can be accessed later. For more details refer README.md."""

import cv2
from pyspark import SparkContext
from pyspark.sql import SparkSession
import numpy as np
import sys
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
	
	#matching queried image with the image in dataset
	matches = bf_matcher.knnMatch(main_img,test_desc, k = 2)
	
	#filtering good matches 
	good_matches = []
	for m,n in matches:
		if m.distance < 0.75* n.distance:
			good_matches.append([m])

	if len(good_matches) >= 10:
		return (file[0],len(good_matches))

#initialising sift object and extracting queried image features
sift = cv2.xfeatures2d.SIFT_create(200,5)
kps,desc = sift.detectAndCompute(cv2.imread(sys_argv[1],0),None)

#initialising images data RDD
image_data = spark_s.read.parquet("<dir location>/image_data.parquet")

#matching features 
matches = image_data.rdd.map(lambda x: match_features(desc,x)).filter(lambda x: x is not None).collect()

print(matches)

match_ids = []

for x in matches:
	match_ids.append(x[0].oid)

print(match_ids)

#saving result to file
with open("out.json","w") as out_f:
	out_f.write(json.dumps({"matches":match_ids}))

print({"matches":match_ids})

 
