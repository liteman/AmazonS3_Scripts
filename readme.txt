This upload_reporty.py script will upload a specified zip file to Amazon S3.

The Amazon S3 bucket is specified in the global variable BUCKET_NAME
The Amazon S3 account is determined by the ACCESS KEY ID found on the local filesystem: ~/.aws/credentials
Use the "aws configure" command referenced below to properly configure ~/.aws/credentials

To get your Access Key ID and the associated secret key- follow the steps here:
https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSGettingStartedGuide/AWSCredentials.html

The SHA256 hash of the zip file will be used as destination "folder" name in the S3 Bucket. The destination
file will always be named "report.zip" (This is a NetRecon Splunk App dependency)

For tracking/reporting purposes, a customer name must be specified on the command-line. This will associate
the SHA256 hash with a customer. The customer name will be added to the Metadata of the uploaded file.

Script Requirements:
pip install boto3

Use AWS CLI to set up the local AWS environment.
    "pip install awscli"
    Shell command: "aws configure"
    This will prompt you for the necessary values

Example usage:

./upload_report.py -f filename.zip -c Name