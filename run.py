import argparse
import yaml
import boto3
import subprocess

import jmespath

import paramiko
import scp

parser = argparse.ArgumentParser()
parser.add_argument("--ami", default="deep_learning_ami_ubuntu18")
parser.add_argument("--instance_type", default="m5.2xlarge")

args = parser.parse_args()


# https://docs.aws.amazon.com/cli/latest/reference/ec2/run-instances.html
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/ec2-example-managing-instances.html
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.run_instances






def launch_instance(ami_id, instance_type):
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

    ec2_client = boto3.client('ec2')
    security_group_id = 'sg-2e1ad256'

    response = ec2_client.run_instances(
        ImageId=ami_id,
        InstanceType=instance_type,
        KeyName='web_app',
        SecurityGroupIds=[security_group_id],
        MaxCount=1,
        MinCount=1
    )

    instance_id = response["Instances"][0]["InstanceId"]
    print("instance_id: {}".format(instance_id))

    ec2_resource = boto3.resource('ec2')
    instance = ec2_resource.Instance(instance_id)
    instance.wait_until_running()
    print("Instance is successfully launched")

    # scp -i "web_app.pem" ubuntu@34.221.118.27:/home/ubuntu/hoge.txt ./hoge.txt

    # with paramiko.SSHClient() as sshc:
    #     sshc.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #     sshc.connect(hostname=instance.public_ip_address, port=22, username='ubuntu', key_filename='/home/matsui/デスクトップ/web_app.pem')
    #
    #     with scp.SCPClient(sshc.get_transport()) as scpc:
    #         scpc.get('/home/ubuntu/annbench/result_img', recursive=True)

    # Terminate the instance
    waiter = ec2_client.get_waiter('instance_terminated')
    print("Try to terminate the instance")
    instance.terminate()

    # Check it's successfully terminated
    waiter.wait(InstanceIds=[instance_id])
    print("Instance is successfully terminated")

    return instance_id, instance.public_ip_address

def ami_image_id(ami):
    # Return the latest AMI ID
    # CLI:
    # aws ec2 describe-images \
    # --owners 'amazon' \
    # --filters 'Name=name,Values=Deep Learning AMI (Ubuntu 18.04)*' \
    # --query 'sort_by(Images, &CreationDate)[-1].[ImageId]' \
    # --output 'text'
    assert ami in ["deep_learning_ami_ubuntu18"]

    name = {'deep_learning_ami_ubuntu18': 'Deep Learning AMI (Ubuntu 18.04)*'}[ami]

    ec2_client = boto3.client('ec2')
    res = ec2_client.describe_images(
        Filters=[{'Name': 'name', 'Values': [name]}],
        Owners=['amazon'],
    )
    # As boto3 doesn't have --query option, we need to mimic the behavior by jmespath
    # https://qiita.com/t_wkm2/items/bdb6890e23a6d0bc9ce7
    res = jmespath.search('sort_by(Images, &CreationDate)[-1].[ImageId]', res)

    return res[0]

if __name__ == '__main__':

    ami_id = ami_image_id(ami=args.ami)
    print("ami_id:", ami_id)
    instance_id, public_ip = launch_instance(ami_id=ami_id,
                                             instance_type=args.instance_type)
    print("instance_id: {}, public_ip: {}".format(instance_id, public_ip))



    #subprocess.run("ssh {}".format(huga), shell=True)
