import time

import boto3
from botocore.exceptions import ClientError


################################################################################################
#
# Configuration Parameters
#
################################################################################################


# place your credentials in ~/.aws/credentials, as mentioned in AWS Educate Classroom,
# Account Details, AWC CLI -> Show (Copy and paste the following into ~/.aws/credentials)

# changed to use us-east, to be able to use AWS Educate Classroom
region = 'us-east-1'
availabilityZone = 'us-east-1a'
# region = 'eu-central-1'
# availabilityZone = 'eu-central-1b'

# AMI ID of Amazon Linux 2 image 64-bit x86 in us-east-1 (can be retrieved, e.g., at
# https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#LaunchInstanceWizard:)
imageId = 'ami-0d5eff06f840b45e9'
# for eu-central-1, AMI ID of Amazon Linux 2 would be:
# imageId = 'ami-0cc293023f983ed53'

# potentially change instanceType to t2.micro for "free tier" if using a regular account
# for production, t3.nano seams better
instanceType = 't2.nano'

keyName = 'cloud_comp5'


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
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
        ])
    print('Ingress Successfully Set %s' % data)
except ClientError as e:
    print(e)


userDataDB = ('#!/bin/bash\n'
              '# extra repo for RedHat rpms\n'
              'yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm\n'
              '# essential tools\n'
              'yum install -y joe htop git\n'
              '# mysql\n'
              'yum install -y mariadb mariadb-server\n'
              '\n'
              'service mariadb start\n'
              '\n'
              'echo "create database db_cloudcomputing" | mysql -u root\n'
              'echo "create table users ( id INT AUTO_INCREMENT, username VARCHAR(150) NOT NULL, password VARCHAR(150) NOT NULL, PRIMARY KEY (id))" | mysql -u root cloud_comp_user\n'
              '\n'
              'echo "create table chats ( id INT AUTO_INCREMENT, name VARCHAR(255) NOT NULL, description VARCHAR(500) NOT NULL, creatorId INT NOT NULL, PRIMARY KEY (id))" | mysql -u root cloud_comp_user\n'
              '\n'
              'echo "create table messages ( id INT AUTO_INCREMENT, userId INT NOT NULL, chatId INT NOT NULL, message VARCHAR(1000) NOT NULL, time_created DATETIME NOT NULL, PRIMARY KEY (id))" | mysql -u root cloud_comp_user\n'
              '\n'
              'echo "CREATE USER \'cloud_comp_user\'@\'%\' IDENTIFIED BY \'demo5\';" | mysql -u root\n'
              'echo "GRANT ALL PRIVILEGES ON cloud_comp_user.* TO \'cloud_comp_user\'@\'%\';" | mysql -u root\n'
              'echo "FLUSH PRIVILEGES" | mysql -u root\n'
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
                     '# extra repo for RedHat rpms\n'
                     'yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm\n'
                     '# essential tools\n'
                     'yum install -y joe htop git\n'
                     '# mysql\n'
                     'yum install -y httpd php php-mysql\n'
                     '\n'
                     'service httpd start\n'
                     '\n'
                     # 'wget http://mmnet.informatik.hs-fulda.de/cloudcomp/StudyChat-in-the-clouds.tar.gz\n'
                     # 'cp StudyChat-in-the-clouds.tar.gz /var/www/html/\n'
                     # 'tar zxvf StudyChat-in-the-clouds.tar.gz\n'
                     'cd /var/www/html\n'
                     'wget https://gogs.informatik.hs-fulda.de/srieger/cloud-computing-msc-ai-examples/raw/master/example-projects/StudyChat-in-the-clouds/web-content/index.php\n'
                     'wget https://gogs.informatik.hs-fulda.de/srieger/cloud-computing-msc-ai-examples/raw/master/example-projects/StudyChat-in-the-clouds/web-content/cloud.php\n'
                     'wget https://gogs.informatik.hs-fulda.de/srieger/cloud-computing-msc-ai-examples/raw/master/example-projects/StudyChat-in-the-clouds/web-content/config.php\n'
                     '\n'
                     '# change hostname of db connection\n'
                     'sed -i s/localhost/' + privateIpDB + '/g /var/www/html/config.php\n'
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
        print("StudyChat-in-the-clouds can be accessed at: " + instance.public_ip_address)
    else:
        print("Could not get public IP using boto3, this is likely an AWS Educate problem. You can however lookup the "
              "public ip from the AWS management console.")