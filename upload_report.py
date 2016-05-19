#!/usr/bin/python
"""
This script will upload a specified zip file to Amazon S3.

The Amazon S3 bucket is specified in the global variable BUCKET_NAME
The Amazon S3 account is determined by the ACCESS KEY ID found on the local filesystem: ~/.aws/credentials

To get your Access Key ID and the associated secret key- follow the steps here:
https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSGettingStartedGuide/AWSCredentials.html

The SHA256 hash of the zip file will be used as destination "folder" name in the S3 Bucket. The destination
file will always be named "report.zip" (This is a NetRecon Splunk App dependency)

For tracking/reporting purposes, a customer name must be specified on the command-line. This will associate
the SHA256 hash with a customer. The customer name and the original file name will be added to the Metadata of
the uploaded file.

Script Requirements:
pip install boto3

Use AWS CLI to set up the local AWS environment.
    "pip install awscli"
    Shell command: "aws configure"
    This will prompt you for the necessary values

Example usage:

./upload_report.py -f filename.zip -c Name


"""

import boto3
import botocore
import argparse
import sys
import hashlib
from datetime import datetime
import zipfile
import os

SSENCRYPT = 'AES256'  # AWS ServerSideEncryption value
REPORT_NAME = 'report.zip'  # Target file name
BUCKET_NAME = 'default'  # Target bucket for file uploads
S3RESOURCE = boto3.resource('s3')  # Resource handle to the S3 Account
S3CLIENT = boto3.client('s3')  # Client handle to the S3 Account
S3_ACL = 'public-read'  # Canned ACL to set on the uploaded file


def newlifecyclerule(prefix):
    """
    Configure the specified prefix to expire and be deleted from Amazon S3 after the
    specified number of days.
    param prefix:The 'folder/filename' to which the Lifecycle rule will apply

    Return:
    Dictionary structure needed for the boto3.s3.bucket_lifecycle.put() method
    """

    lifecycleid = prefix.split('/')[0]

    lifecycle = dict(Status='Enabled',
                     Prefix=prefix,
                     Expiration={u'Days': 3},
                     ID=lifecycleid)

    return lifecycle


def setLifecycleConfig(prefix):
    """
    Get the existing lifecycle configuration from the bucket.
    Append a new lifecycle rule.
    Set the new lifecycle configuration on the bucket.

    :param prefix:
    :return: none
    """
    # Get a handle to the target Bucket
    bucket_lifecycle = S3RESOURCE.BucketLifecycle(BUCKET_NAME)

    # Get the current bucket lifecycle configuration
    try:
        bucket_lifecycle_cfg = S3CLIENT.get_bucket_lifecycle_configuration(Bucket=BUCKET_NAME)
    except botocore.exceptions.ClientError as e:
        if '(NoSuchLifecycleConfiguration)' in str(e):
            bucket_lifecycle_cfg = dict(Rules=[])
        else:
            print "Error getting lifecycle configuration: " + str(e)
            sys.exit(1)

    # Remove this trailing dictionary element from the set of rules
    # This won't exist if we there were not existing lifecycle rules
    try:
        bucket_lifecycle_cfg.pop('ResponseMetadata')
    except KeyError:
        pass

    # If a lifecycle rule already exists for this folder/file then remove it
    # and append a new rule to the lifecycle configuration Rules list-element
    index = None
    for i in range(len(bucket_lifecycle_cfg['Rules'])):
        if bucket_lifecycle_cfg['Rules'][i].get('ID') == prefix.split("/")[0]:
            index = i

    if index is not None:
        del bucket_lifecycle_cfg['Rules'][index]  # Remove the existing rule from the local copy
        bucket_lifecycle.delete()  # Clear all existing rules on S3

    bucket_lifecycle_cfg['Rules'].append(newlifecyclerule(prefix))  # Add new rule to the local copy

    # Upload new lifecycle configuration
    try:
        bucket_lifecycle.put(
            LifecycleConfiguration=bucket_lifecycle_cfg)
    except botocore.exceptions.ClientError as e:
        print "Error with lifecycle configuration: " + str(e)


def uploadToS3(filename, targetfolder, customer, contenttype='application/zip'):
    """
    Upload the specified file to the S3 bucket, set appropriate permissions, and enable encryption.

    :param filename: Local path for the file to be uploaded
    :param targetfolder: Folder to be created in the bucket
    :param contenttype: The mime-type of the file to be uploaded. Necessary for proper downloads later.

    :return: String containing the target folder/filename
    """

    prefix = targetfolder + "/" + REPORT_NAME

    # Upload file
    with open(filename, 'rb') as filedata:
        upload = S3CLIENT.put_object(Body=filedata,  # local filename/path
                                     Bucket=BUCKET_NAME,  # Target S3 bucket
                                     Key=prefix,  # key (Target folder/filename)
                                     ACL=S3_ACL,  # Canned Permissions to set on the file
                                     ContentType=contenttype,
                                     ServerSideEncryption=SSENCRYPT,
                                     Metadata={'customer': customer,
                                               'originalFile': os.path.basename(filename)})

    # If the upload is unsuccessful (HTTPStatusCode is not 200) then die...
    if upload['ResponseMetadata']['HTTPStatusCode'] != 200:
        print "Upload failed - HTTPStatusCode " + str(upload['ResponseMetadata']['HTTPStatusCode'])
        sys.exit(1)
    else:
        print "Upload Successful"

    return prefix


def verifyzip(filename):

    try:
        zipf = zipfile.ZipFile(filename)
        zipf.testzip()
    except IOError as e:
        print e
        sys.exit(1)
    except zipfile.BadZipfile as e:
        print "Error: " + str(e) + " " + filename
        sys.exit(1)


def getFolderName(filename):
    """

    :param filename: Path to the file to upload
    :return: String containing the hash of the specified file
    """

    # Call function to verify the specified file exists
    # and that it is a zip file

    verifyzip(filename)

    block = 1024

    with open(filename, 'rb') as datafile:
        # read in a buffer of size block
        buf = datafile.read(block)

        # Create hash object to use SHA256
        hashobj = hashlib.sha256()

        # while file has more bytes, update the hash
        while len(buf) > 0:
            hashobj.update(buf)
            buf = datafile.read(block)

        return str(hashobj.hexdigest())


def main():

    parser = argparse.ArgumentParser(description="NetRecon Zip to S3 - Uploader")
    parser.add_argument("-f",
                        "--file",
                        required=True,
                        help="Filename (or path) of local zip file to upload")
    parser.add_argument("-c",
                        "--customer",
                        required=True,
                        help="Customer name associated with the specified file")

    args = parser.parse_args()
    filename = args.file
    customer = args.customer

    # generate the folder name based on the SHA256 hash of the file
    targetfolder = getFolderName(filename)

    # Upload file and capture the prefix and timestamp
    prefix = uploadToS3(filename, targetfolder, customer)
    uploadtimestamp = str(datetime.now())

    # Set lifecycle of the uploaded file
    setLifecycleConfig(prefix)

    # log the upload
    print ','.join([uploadtimestamp, customer, os.path.basename(filename), targetfolder])


if __name__ == '__main__':
    main()
