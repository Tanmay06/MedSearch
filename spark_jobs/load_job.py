import cv2
import numpy as np
from pyspark.sql import SparkSession
from pyspark import SparkContext
#from pyspark import SaveMode

#initialising SparkContext
spark_c = SparkContext()

#function to extract features from images
def extract_feature(case_data):
	#initializing SIFT object, the deature threshold is kept 200 and octave layers to 5
	sift = cv2.xfeatures2d.SIFT_create(200,5)

	#converting raw binary to numpy array and the reading image to extract descriptors using sift
	img_array = np.asarray(bytearray(case_data[1]),dtype=np.uint8)
	img = cv2.imdecode(img_array,0)# 0 argument tells to read in grayscale
	kps,desc = sift.detectAndCompute(img,None)
	print("---%s---Features extracted"%(case_data[0]))
	return(case_data[0],bytearray(desc),desc.shape)


#creating spark session object to connect with MongoDB clusters
spark_s = SparkSession\
.builder\
.appName("Get Data from DB")\
.config("spark.mongodb.input.uri","mongodb://userdata:userdata@medsearchcluster-shard-00-00-5lyma.mongodb.net:27017,medsearchcluster-shard-00-01-5lyma.mongodb.net:27017,medsearchcluster-shard-00-02-5lyma.mongodb.net:27017/test_db.cases?ssl=true&replicaSet=MedSearchCluster-shard-0&authSource=admin")\
.getOrCreate()

#Loading or importing data from MongoDB cluster
cases_data_frame = spark_s.read.format("com.mongodb.spark.sql.DefaultSource").load()

#converting dataframe to RDD and extracting features from images
cases_data_RDD = cases_data_frame.select("_id","data").rdd.map(lambda x: extract_feature(x)).cache()

#converting back to dataframe and writing to parquet file   
spark_s.createDataFrame(cases_data_RDD,["_id","descriptors","shape"]).write.mode("overwrite").parquet("image_data.parquet")
