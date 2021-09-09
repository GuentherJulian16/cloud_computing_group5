import boto3
from botocore.exceptions import ClientError

region = 'us-east-1'

client = boto3.setup_default_session(region_name=region)
ec2Client = boto3.client("ec2")
ec2Resource = boto3.resource('ec2')


print("Deleting old instances...")
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
