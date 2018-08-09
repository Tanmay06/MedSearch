# MedSearch
<p>It is a content based image retrieval system which uses MongoDB to store data and, Apache Spark to process the stored data and generate results. The image dataset is stored in MongoDB Cluster, which is imported by a Spark job and the features of these images is calculated and stored in HDFS along with their respective MongoDB Objed_Id. When a image search request is received another Spark job calculates the features of the queried image and matches it with that stored on the HDFS. The Object_Id of matching images is sent back in response to the request, these Object_Ids can be then used to fetch images from the database.</p>
<h2>System Architecture</h2>
<p>The entire system is divided in three tiers:</p>
<ol>
  <li>Processing Level (Spark and MongoDB Clusters)</li>
  <li>API Level (API Managing Server)</li>
  <li>UI Level (Devices Accessing API)</li>
  </ol>
<p>The <b>Processing Level</b> consists of the Spark Cluster and the MongoDB Cluster. The master node of Spark cluster also runs a Python based single threded Simple HTTP Server which handles the image search requests from the API Level.</p>
<p>The <b>API Level</b> acts as abstraction over the Processing Layer for the UI Layer so that the user can access different functionalities using simple API. The API Layer is a single threaded python based Simple HTTP Server which offers communication medium for querying the database, searching for image using Spark, posting image to the database,etc.</p>
<p>The <b>UI Level</b> consists of the devices which consumes the API and uses the system. This system was tested using Android Application and the source for the same is not included in the repository.</p>
<h2>Directory and Files</h2>
<ul>
  <li><p><a href="https://github.com/Tanmay06/MedSearch/tree/master/bash_service">/bash_service</a> it contains script to run the python servers as linux services. <a href="https://www.raspberrypi-spy.co.uk/2015/10/how-to-autorun-a-python-script-on-boot-using-systemd/">Here</a> you can find more information on how to run a python script as a service on linux.</p>
  </li>
  <li><p><a href="https://github.com/Tanmay06/MedSearch/tree/master/server_scripts">/server_scripts</a> contains scripts to to run python server on API server as well as the Spark cluster's masternode.</p>
    <ul>
      <li><p><a href="https://github.com/Tanmay06/MedSearch/blob/master/server_scripts/mid_server.py">mid_server.py</a> runs python server on the API server.</p>
      </li>
      <li><p><a href="https://github.com/Tanmay06/MedSearch/blob/master/server_scripts/spark_server.py">spark_server.py</a> runs python server on the Spark cluster's masternode.</p>
      </li>
    </ul>
  </li>
  <li><p><a href="https://github.com/Tanmay06/MedSearch/tree/master/spark_jobs">/spark_jobs</a> contains Spark jobs to fetch images fron database and extract features, and search for queried image by matching features.</p>
    <ul>
      <li><p><a href="https://github.com/Tanmay06/MedSearch/blob/master/spark_jobs/load_job.py">load_job.py</a> spark job to load images from MongoDB, extract features and store on local HDFS.
      </li>
      <li><p><a href="https://github.com/Tanmay06/MedSearch/blob/master/spark_jobs/match.py">match.py</a> spark job to extract features of queried image, match that with stored features and return Object_Ids of the matches.</p>
      </li>
    </ul>
  </li>
</ul>
<h2>Prerequisites and Working Environment</h2>
<ul>
  <li><p><a href="https://www.python.org/downloads/">Python 3.0+</a></p></li>
  <li><p><a href="https://pypi.org/project/opencv-python/">OpenCV 2.0+</a></p></li>
  <li><p><a href="https://spark.apache.org/docs/latest/api/python/index.html">Pyspark 2.3.0+</a></p></li>
  <li><p><a href="http://spark.apache.org">Apache Spark 2.0+</a></p></li>
  <li><p><a href="https://www.mongodb.com/cloud/atlas">MongoDB Atlas 3.6.6</a></p></li>
</ul>
<p>The Apache Spark cluster was built using <a href="https://cloud.google.com/dataproc/">Google Cloud DataProc</a> on <b>YARN</b> and the API server was a standalone <a href="https://cloud.google.com/compute/docs/">Google Compute Engine</a>. If you want you can use similar setup and tools for running the system or else you can go for a different approach with some little tweaks.</p>
<h2>Process Logic and Running the System</h2>
<p>As mentioned before the images' dataset is stored on MongoDB cluster. As this system was meant to use medical images dataset uploaded by the users, the document schema for dataset collection used by the system is as follows:</p>

```
{
  'name': 'Image name',
  'tags': ['tag1', 'tag2'], 
  'uploader': {
    'u_id':ObjectId() #user's Id,
    'u_name': 'User Name'
    }, 
  'description': 'case description',
  'data': Bindata()#Image in binary, 
  '_id':ObjectId() #image case id
 }
```

<p>To move forward it is assumed that you have your Apache Spark and, MongoDB clusters up and running. If they are not you can refer the following links for help.</p>
<ul>
  <li><a href="https://cloud.google.com/dataproc/docs/guides/create-cluster">Setting up Apache Spark on Google Cloud Data Proc</a> select Pyspark while setting up the cluster.
  </li>
  <li><a href="https://docs.mongodb.com/spark-connector/current/python-api/">Spark MongoDB Connector</a> for Pyspark to communicate with MongoDB.
  </li>
  <li><a href="https://stackoverflow.com/questions/30518362/how-do-i-set-the-drivers-python-version-in-spark">Setting up default Python for all spark nodes.</a></li>
</ul>
<p>Firstly the system requires the collection of features and Object_Ids of the images in the dataset. To do this run <a href="https://github.com/Tanmay06/MedSearch/blob/master/spark_jobs/load_job.py">load_job.py</a> using `spark-submit`. This job will load images from the database, calculate its features and will store the features along with Object_ids in <b>image_data.parquet</b> file on <b>HDFS</b>. <b>SIFT</b> feature detection and extraction algorithm provided in OpenCV is used to extract features of the images. This spark job is not automated yet, but should be run at regular intervals to keep the image_data.parquet up to date with the date base.</p>
<p>Once image_data.parquet is generated, start <a href="https://github.com/Tanmay06/MedSearch/blob/master/server_scripts/mid_server.py">mid_server.py</a> at API server and <a href="https://github.com/Tanmay06/MedSearch/blob/master/server_scripts/spark_server.py">spark_server.py</a> at spark cluster's master node. Verify the Spark cluster's masternode url which is serving spark_server.py in mid_server.py. Move <a href="https://github.com/Tanmay06/MedSearch/blob/master/spark_jobs/match.py">match.py</a> to home directory of your masternode. The system is now ready to serve the API. The requests are made to the API server which forwards it to the Spark cluster or the MongoDB cluster. API server currently handles POST and GET requests which provides services like search for image, post image in database, secured user login, and fetch images directly from database using the Object_Id.</p>
<p>The GET method is currently used only for fetching image detials using the Object_Id but the POST method handles different requests using the action parameter. Detailed use of POST, GET methods, and action parameter is described below.</p>

```
GET <url>?objectid="MongoDB case objectid in string"
```

```
POST <url>?action=login
{"uname":"username",
  "password":"password"}
```

```
POST <url>?action=search_case
<image to be searched in binary>
```

```
POST <url>?action=post_case
{
  'name': 'Image name',
  'tags': ['tag1', 'tag2'], 
  'uploader': {
    'u_id':ObjectId() #user's Id,
    'u_name': 'User Name'
    }, 
  'description': 'case description',
  'data': Bindata()#Image in binary, 
  '_id':ObjectId() #image case id
 }
```

<p>This API was developed for Android Application but can be used for applications which can consume HTTP based API as it was tested using <a href="https://www.getpostman.com">Postman</a></p>
<p>When the API recieves a image search request it forwards it to the Spark server which downloads the image locally and starts spark-submit as subprocess with match.py and queried image as arguments. The Spark job extract features from queried image and loads features from image_data.parquet. Brute Force matching using Eucledian distance over KNN is used to match fetures of queried image with that of images in dataset. The object_ids of matched images is stored in a json and forwarded to API server.</p>
<p>The API server, once json is received, fetches the matching images from database, compresses them to thumbnails and sends them to the requesting user along with their object_ids. The user can use the object_id to get full details of the image.</p>
