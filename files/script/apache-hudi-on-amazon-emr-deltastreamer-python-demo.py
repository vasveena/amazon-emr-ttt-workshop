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
# Replace with your own bucket
s3_bucket = "mrworkshop-youraccountID-dayone"
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
        print(f)
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
            print ("old address: " + rec['street_address'])
            rec['street_address'] = fake.address()
            print ("new address: " + rec['street_address'])
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

generate_bulk_data()

generate_updates()
