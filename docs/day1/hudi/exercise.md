# ** Exercise 4 - Apache Hudi on Amazon EMR **

In this exercise you will build incremental data lakes on EMR using Apache Hudi. You can build data lakes using Apache Hudi using Spark Datasource APIs, Hudi Deltastreamer utility and SparkSQL.  

In the previous EMR Studio exercise, we linked the Git repository in the Jupyter interface. We will continue to use the same repository to run these exercises.

SSH into the EMR leader node of the cluster "EMR-Spark-Hive-Presto" or open a session using AWS Session Manager for the EMR leader node since we will be running a few commands directly on the leader node.

### Apache Hudi with Spark Datasource APIs

Open the file workshop-repo -> files -> notebook -> apache-hudi-on-amazon-emr-datasource-pyspark-demo.ipynb in the Jupyter. Make sure the Kernel is set to PySpark.

![Hudi - 1](images/hudi-1.png)

All the instructions required to run the notebook are within the notebook itself.

Download the file workshop-repo -> schema -> schema.avsc to your local desktop and upload this file into the following S3 location (replace "youraccountID" with your event engine AWS account ID): *s3://mrworkshop-youraccountID-dayone/schema/schema.avsc*

![Hudi - 2](images/hudi-2.png)

Alternatively, you can run the following commands from the leader node of your EMR cluster. Replace "youraccountID" with your event engine AWS account ID. We will be using this schema AVRO file to run compaction on Merge-On-Read tables.

```
sudo su hadoop
cd ~
curl -o schema.avsc https://raw.githubusercontent.com/vasveena/amazon-emr-ttt-workshop/main/files/schema/schema.avsc
aws s3 cp schema.avsc s3://mrworkshop-youraccountID-dayone/schema/schema.avsc
```

Run the blocks of the notebook "apache-hudi-on-amazon-emr-datasource-pyspark-demo.ipynb". Replace "youraccountID" in the S3 paths within the notebook with your AWS event engine account ID.

### Apache Hudi with Spark Deltastreamer

Hudi provides a utility called Deltastreamer for creating and manipulating Hudi datasets without the need to write any Spark code. For this activity, let us copy a few files to the S3 location. Run the following commands in your EMR leader node session created using Session Manager or SSH.

```
sudo su hadoop
cd ~
curl -o source-schema-json.avsc https://raw.githubusercontent.com/vasveena/amazon-emr-ttt-workshop/main/files/schema/source-schema-json.avsc
curl -o target-schema-json.avsc https://raw.githubusercontent.com/vasveena/amazon-emr-ttt-workshop/main/files/schema/target-schema-json.avsc
curl -o json-deltastreamer.properties https://raw.githubusercontent.com/vasveena/amazon-emr-ttt-workshop/main/files/properties/json-deltastreamer.properties
curl -o json-deltastreamer_upsert.properties https://raw.githubusercontent.com/vasveena/amazon-emr-ttt-workshop/main/files/properties/json-deltastreamer_upsert.properties

```

Replace youraccountID with event engine AWS account ID in the files json-deltastreamer.properties and json-deltastreamer_upsert.properties. You can do so using sed command below. Replace 707263692290 with your event engine account ID.

```
sed -i 's|youraccountID|707263692290|g' json-deltastreamer.properties
sed -i 's|youraccountID|707263692290|g' json-deltastreamer_upsert.properties
```

Now, copy the four files to your S3 location. Replace youraccountID with event engine AWS account ID.

```
aws s3 cp source-schema-json.avsc s3://mrworkshop-youraccountID-dayone/hudi-ds/config/
aws s3 cp target-schema-json.avsc s3://mrworkshop-youraccountID-dayone/hudi-ds/config/
aws s3 cp json-deltastreamer.properties s3://mrworkshop-youraccountID-dayone/hudi-ds/config/
aws s3 cp json-deltastreamer.properties s3://mrworkshop-youraccountID-dayone/hudi-ds/config/

```

Now let's generate some Fake data for the purpose of this workshop. We will use [Faker](https://faker.readthedocs.io/en/master/) library for that. Install Faker with the below command. 

```
pip install Faker
```

Open a Python shell in your EMR leader node session by typing "python".

![Hudi - 3](images/hudi-3.png)

Run the following block to generates some fake data. Replace youraccountID with event engine AWS account ID.

```
import os
import json
import random
import boto3
import io
from io import StringIO
from faker import Faker
from faker.providers import date_time, credit_card
from json import dumps


# Intialize Faker library and S3 client
fake = Faker()
fake.add_provider(date_time)
fake.add_provider(credit_card)

s3 = boto3.resource('s3')

# Write the fake profile data to a S3 bucket
# REPLACE youraccountID with event engine AWS account ID
s3_bucket = "mrworkshop-707263692290-dayone"
s3_load_prefix = 'hudi-ds/inputdata/'
s3_update_prefix = 'hudi-ds/updates/'

# Number of records in each file and number of files
# Adjust per your need - this produces 40MB files
#num_records = 150000
#num_files = 50

num_records = 10000
num_files = 15

def generate_bulk_data():
    '''
    Generates bulk profile data
    '''
    # Generate number of files equivalent to num_files
    for i in range (num_files):
        fake_profile_data = fake_profile_generator(num_records, fake)
        fakeIO = StringIO()
        filename = 'profile_' + str(i + 1) + '.json'
        s3key = s3_load_prefix + filename
        fakeIO.write(str(''.join(dumps_lines(fake_profile_data))))
        s3object = s3.Object(s3_bucket, s3key)
        s3object.put(Body=(bytes(fakeIO.getvalue().encode('UTF-8'))))
        fakeIO.close()

def generate_updates():
    '''
    Generates updates for the profiles
    '''
    #
    # We will make updates to records in randomly picked files
    #
    random_file_list = []
    for i in range (1, num_files):
        random_file_list.append('profile_' + str(i) + '.json')
    for f in random_file_list:
        #print(f)
        s3key = s3_load_prefix + f
        obj = s3.Object(s3_bucket, s3key)
        profile_data = obj.get()['Body'].read().decode('utf-8')
        #s3_profile_list = json.loads(profile_data)
        stringIO_data = io.StringIO(profile_data)
        data = stringIO_data.readlines()
        #Its time to use json module now.
        json_data = list(map(json.loads, data))
        fakeIO = StringIO()
        s3key = s3_update_prefix + f
        fake_profile_data = []
        for rec in json_data:
            # Let's generate a new address
            #print ("old address: " + rec['street_address'])
            rec['street_address'] = fake.address()
            #print ("new address: " + rec['street_address'])
            fake_profile_data.append(rec)       
        fakeIO.write(str(''.join(dumps_lines(fake_profile_data))))
        s3object = s3.Object(s3_bucket, s3key)
        s3object.put(Body=(bytes(fakeIO.getvalue().encode('UTF-8'))))
        fakeIO.close()

def fake_profile_generator(length, fake, new_address=""):
    """
    Generates fake profiles
    """
    for x in range (length):       
        yield {'Name': fake.name(),
               'phone': fake.phone_number(),
               'job': fake.job(),
               'company': fake.company(),
               'ssn': fake.ssn(),
               'street_address': (new_address if new_address else fake.address()),
               'dob': (fake.date_of_birth(tzinfo=None, minimum_age=21, maximum_age=105).isoformat()),
               'email': fake.email(),
               'ts': (fake.date_time_between(start_date='-10y', end_date='now', tzinfo=None).isoformat()),
               'credit_card': fake.credit_card_number(),
               'record_id': fake.pyint(),
               'id': fake.uuid4()}

def dumps_lines(objs):
    for obj in objs:
        yield json.dumps(obj, separators=(',',':')) + '\n'
```

Now, let us run the function in the same python shell to generate bulk insert data and upsert data in the respective S3 locations.

```
generate_bulk_data()
generate_updates()

```
