#!/usr/bin/python
"""

This script lists all objects (files) currently residing in the bucket specified by global variable BUCKET_NAME
Each line will contain the path to the object (key), Object Metadata, last-modified time of the object, and
the expiration date of the object as well as the rule-id which specified the expiration time.

Rules are set at the bucket level.

"""

import boto3

BUCKET_NAME = 'mybucket'
S3RESOURCE = boto3.resource('s3')
BUCKETOBJ = S3RESOURCE.Bucket(BUCKET_NAME)

for objsummary in BUCKETOBJ.objects.all():
    s3object = S3RESOURCE.Object(BUCKET_NAME, objsummary.key)
    print ','.join([objsummary.key, str(s3object.metadata), str(s3object.last_modified), str(s3object.expiration)])

