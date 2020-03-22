import argparse
import yaml
import boto3

import paramiko
import scp

parser = argparse.ArgumentParser()
args = parser.parse_args()


# https://docs.aws.amazon.com/cli/latest/reference/ec2/run-instances.html
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/ec2-example-managing-instances.html
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.run_instances


# Corresponding CLI:
# aws ec2 run-instances \
#     --image-id ami-0d1cd67c26f5fca19 \
#     --count 1 \
#     --instance-type t2.micro \
#     --key-name web_app \
#     --security-group-ids sg-2e1ad256 \
#     --block-device-mappings file://mapping.json \
#     --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=234}]'

# with "mapping.json":
# [
#     {
#         "DeviceName": "/dev/sda1",
#         "Ebs": {
#             "VolumeSize": 1000
#         }
#     }
# ]




def launch_instance(ami, instance_type, user_data):
    ec2_client = boto3.client('ec2')

    # Need to convert from ami to imageId

    # Set name

    response = ec2_client.run_instances(
        ImageId='ami-008d8ed4bd7dc2485',
        InstanceType=instance_type,
        KeyName='web_app',
        SecurityGroupIds=[
            'sg-2e1ad256',
        ],
        MaxCount=1,
        MinCount=1,
        UserData=user_data
    )

    instance_id = response["Instances"][0]["InstanceId"]
    print("instance_id: {}".format(instance_id))

    ec2_resource = boto3.resource('ec2')
    instance = ec2_resource.Instance(instance_id)
    instance.wait_until_running()

    # scp -i "web_app.pem" ubuntu@34.221.118.27:/home/ubuntu/hoge.txt ./hoge.txt

    with paramiko.SSHClient() as sshc:
        sshc.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sshc.connect(hostname=instance.public_ip_address, port=22, username='ubuntu')#, key_filename='../web_app.pem')

        with scp.SCPClient(sshc.get_transport()) as scpc:
            scpc.get('/home/ubuntu/hoge.txt')

    # Terminate!
    #instance.terminate()

    return instance_id, instance.public_ip_address

if __name__ == '__main__':

    ami = "xxx"
    instance_type = "m5.2xlarge"
    user_data = '''#!/bin/bash
pwd
pwd > /home/ubuntu/hoge.txt
ls
ls > /home/ubuntu/huga.txt'''
    #instance_id, public_ip = launch_instance(ami=ami, instance_type=instance_type, user_data=user_data)
    #print("instance_id: {}, public_ip: {}".format(instance_id, public_ip))
    print("hogehoge")

