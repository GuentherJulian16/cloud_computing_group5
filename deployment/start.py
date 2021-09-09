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


# IMPORTANT
# place your credentials in ~/.aws/credentials, as mentioned in AWS Educate Classroom,
# Account Details, AWC CLI -> Show (Copy and paste the following into ~/.aws/credentials)

# use us-east, to be able to use AWS Educate Classroom
region = 'us-east-1'
availabilityZone = 'us-east-1a'

#Amazon Linux 2 image 64-bit x86 in us-east-1
#imageId = 'ami-0d5eff06f840b45e9'
#Ubuntu 20.04 image 64-bit x86 in us-east-1
imageId = 'ami-09e67e426f25ce0d7'

instanceType = 't2.small'

keyName = 'cloud_comp5'


# IMPORTANT
# We use Amazon AWS Secret Manager to retrieve the user and password for the database connection
# If you don't want to use the Secret Manager, just set both variables to static strings
#database_user = "yourUserName"
#database_password = "yourPassword"
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

# if you only have one VPC, vpc_id can be retrieved using:
response = ec2Client.describe_vpcs()
vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
# if you have more than one VPC, vpc_id should be specified, and code
# top retrieve VPC id below needs to be commented out
# vpc_id = 'vpc-eedd4187'

subnet_id = ec2Client.describe_subnets(
    Filters=[
        {
            'Name': 'availability-zone', 'Values': [availabilityZone]
        }
    ])['Subnets'][0]['SubnetId']

print("Deleting old instance...")
print("------------------------------------")

response = ec2Client.describe_instances(Filters=[{'Name': 'tag-key', 'Values': ['StudyChat']}])
print(response)
reservations = response['Reservations']
for reservation in reservations:
    for instance in reservation['Instances']:
        if instance['State']['Name'] == "running" or instance['State']['Name'] == "pending":
            response = ec2Client.terminate_instances(InstanceIds=[instance['InstanceId']])
            print(response)
            instanceToTerminate = ec2Resource.Instance(instance['InstanceId'])
            instanceToTerminate.wait_until_terminated()

print("Delete old security group...")
print("------------------------------------")

try:
    response = ec2Client.delete_security_group(GroupName='StudyChat')
except ClientError as e:
    print(e)

print("Create security group...")
print("------------------------------------")

try:
    response = ec2Client.create_security_group(GroupName='StudyChat',
                                               Description='StudyChat',
                                               VpcId=vpc_id)
    security_group_id = response['GroupId']
    print('Security Group Created %s in vpc %s.' % (security_group_id, vpc_id))

    data = ec2Client.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {'IpProtocol': 'tcp',
             'FromPort': 3306,
             'ToPort': 3306,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp',
             'FromPort': 22,
             'ToPort': 22,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp',
             'FromPort': 80,
             'ToPort': 80,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp',
             'FromPort': 443,
             'ToPort': 443,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp',
             'FromPort': 3000,
             'ToPort': 3000,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        ])
    print('Ingress Successfully Set %s' % data)
except ClientError as e:
    print(e)


userDataDB = ('#!/bin/bash\n'
              '# essential tools\n'
              'sudo apt-get update'
              '\n'
              'sudo apt-get install -y htop git\n'
              '# mysql\n'
              'sudo apt-get install -y mysql-server\n'
              '\n'
              'sudo sed -i "s/bind-address.*/bind-address = 0.0.0.0/" /etc/mysql/mysql.conf.d/mysqld.cnf\n'
              '\n'
              'service mysql start\n'
              '\n'
              'echo "create database db_cloudcomputing" | mysql -u root\n'
              'echo "create table users ( id INT AUTO_INCREMENT, username VARCHAR(150) NOT NULL, password VARCHAR(150) NOT NULL, PRIMARY KEY (id))" | mysql -u root db_cloudcomputing\n'
              '\n'
              'echo "create table chats ( id INT AUTO_INCREMENT, name VARCHAR(255) NOT NULL, description VARCHAR(500) NOT NULL, creatorId INT NOT NULL, PRIMARY KEY (id))" | mysql -u root db_cloudcomputing\n'
              '\n'
              'echo "create table messages ( id INT AUTO_INCREMENT, userId INT NOT NULL, chatId INT NOT NULL, message VARCHAR(1000) NOT NULL, time_created DATETIME NOT NULL, PRIMARY KEY (id))" | mysql -u root db_cloudcomputing\n'
              '\n'
              'echo "CREATE USER \'' + database_user + '\'@\'%\' IDENTIFIED WITH mysql_native_password BY \'' + database_password + '\';" | mysql -u root\n'
              'echo "GRANT ALL PRIVILEGES ON db_cloudcomputing.* TO \'' + database_user + '\'@\'%\';" | mysql -u root\n'
              'echo "FLUSH PRIVILEGES" | mysql -u root\n'
              '\n'
              'sudo /etc/init.d/mysql restart\n'
              '\n'
              )
# convert user-data from script with: cat install-mysql | sed "s/^/'/; s/$/\\\n'/"

print("Running new DB instance...")
print("------------------------------------")

response = ec2Client.run_instances(
    ImageId=imageId,
    InstanceType=instanceType,
    Placement={'AvailabilityZone': availabilityZone, },
    KeyName=keyName,
    MinCount=1,
    MaxCount=1,
    UserData=userDataDB,
    SecurityGroupIds=[
        security_group_id,
    ],
    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {'Key': 'Name', 'Value': 'StudyChat-db1'},
                {'Key': 'StudyChat', 'Value': 'db'}
            ],
        }
    ],
)

instanceIdDB = response['Instances'][0]['InstanceId']
privateIpDB = response['Instances'][0]['PrivateIpAddress']
# privateIpDB = response['Instances'][0]['NetworkInterfaces'][0]['NetworkInterfaceId']

instance = ec2Resource.Instance(instanceIdDB)
instance.wait_until_running()

print(instanceIdDB)

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

for i in range(1, 3):
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
                    {'Key': 'Name', 'Value': 'StudyChat-webserver' + str(i)},
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
