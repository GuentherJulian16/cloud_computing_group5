import time
import boto3
import json
from botocore.exceptions import ClientError

def get_secret(secret_key: str):

    secret_name = "CloudComputing/StudyChat"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = json.loads(get_secret_value_response['SecretString'])
            return secret[secret_key]

region = 'us-east-1'
availabilityZone = 'us-east-1b'
imageId = 'ami-09e67e426f25ce0d7'
instanceType = 't2.small'
keyName = 'cloud_comp5'

database_user = get_secret("database_user")
database_password = get_secret("database_password")


################################################################################################
#
# boto3 code
#
################################################################################################


client = boto3.setup_default_session(region_name=region)
ec2Client = boto3.client("ec2")
ec2Resource = boto3.resource('ec2')

response = ec2Client.describe_security_groups(Filters=[{'Name': 'group-name', 'Values': ['StudyChat']}])
security_group_id = response.get('SecurityGroups', [{}])[0].get('GroupId', '')

print("Getting DB IP...")
print("------------------------------------")

response = ec2Client.describe_instances(Filters=[{'Name': 'tag:StudyChat', 'Values': ['db']}])
print(response)
reservations = response['Reservations']
for reservation in reservations:
    for instance in reservation['Instances']:
        if instance['State']['Name'] == "running" or instance['State']['Name'] == "pending":
            instanceDB = ec2Resource.Instance(instance['InstanceId'])
            privateIpDB = instanceDB.private_ip_address

userDataWebServer = ('#!/bin/bash\n'
                     '# essential tools\n'
                     'sudo apt-get update'
                     '\n'
                     'sudo apt-get install -y htop git\n'
                     '# nodejs\n'
                     'curl -fsSL https://deb.nodesource.com/setup_14.x | sudo -E bash -\n'
                     'sudo apt-get install -y nodejs\n'
                     '\n'
                     'git clone https://github.com/GuentherJulian16/cloud_computing_group5.git\n'
                     '\n'
                     'cd cloud_computing_group5\n'
                     'npm install\n'
                     '# change hostname of db connection\n'
                     'sed -i s/localhost/' + privateIpDB + '/g models/db.js\n'
                     'sed -i s/username/' + database_user + '/g models/db.js\n'
                     'sed -i s/userpassword/' + database_password + '/g models/db.js\n'
                     'node app.js\n'
                     )

index = 1
instance_name = ""
while(instance_name == ""):
    response = ec2Client.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': ['StudyChat-webserver' + str(index)]}])
    if(response['Reservations']):
        index = index + 1
    else:
        instance_name = "StudyChat-webserver" + str(index)

print("Running new Web Server instance...")
print("------------------------------------")

response = ec2Client.run_instances(
    ImageId=imageId,
    InstanceType=instanceType,
    Placement={'AvailabilityZone': availabilityZone, },
    KeyName=keyName,
    MinCount=1,
    MaxCount=1,
    UserData=userDataWebServer,
    SecurityGroupIds=[
        security_group_id,
    ],

    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {'Key': 'Name', 'Value': instance_name},
                {'Key': 'StudyChat', 'Value': 'webserver'}
            ],
        }
    ],
)

instanceIdWeb = response['Instances'][0]['InstanceId']

instance = ec2Resource.Instance(instanceIdWeb)
instance.wait_until_running()
instance.load()
# sometimes even after reloading instance details, public IP cannot be retrieved using current boto3 version and
# AWS Educate accounts, try for 10 secs, and ask user to get it from AWS console otherwise
timeout = 10
while instance.public_ip_address is None and timeout > 0:
    print("Waiting for public IP to become available...")
    instance.load()
    time.sleep(1)
    timeout -= 1
if instance.public_ip_address is not None:
    print("StudyChat can be accessed at: http://" + instance.public_ip_address + ":3000")
else:
    print("Could not get public IP using boto3, this is likely an AWS Educate problem. You can however lookup the "
            "public ip from the AWS management console.")

