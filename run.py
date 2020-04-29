import argparse
import boto3
import jmespath
import paramiko
import scp

parser = argparse.ArgumentParser()
parser.add_argument("--ami", default="deep_learning_ami_ubuntu18")
parser.add_argument("--instance_type", default="c5.4xlarge")
parser.add_argument("--ssh_key", default='/home/matsui/デスクトップ/web_app.pem')
parser.add_argument("--scp_trg", default='/home/ubuntu/annbench/result_img')

args = parser.parse_args()


# https://docs.aws.amazon.com/cli/latest/reference/ec2/run-instances.html
# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/ec2-example-managing-instances.html
# https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.run_instances


commands = [
    "git clone https://github.com/matsui528/annbench.git",
    "cd annbench",
    "pip install -r requirements.txt",
    "conda install faiss-cpu -y -c pytorch",
    "python download.py --multirun dataset=siftsmall,sift1m",
    "python run.py --multirun dataset=siftsmall,sift1m algo=linear,annoy,ivfpq,hnsw",
    "python plot.py"
]



def launch_instance(ami_id, instance_type, ssh_key, scp_trg):
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

    # SSH into the machine, run the commands
    with paramiko.SSHClient() as sshc:
        sshc.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sshc.connect(hostname=instance.public_ip_address, port=22, username='ubuntu',
                     key_filename=ssh_key)

        # is_alive check: https://stackoverflow.com/a/28288598
        is_alive = sshc.get_transport() is not None and sshc.get_transport().is_active()
        assert is_alive

        cmd = ";".join(commands)  # Need to join because we cannot "cd" in paramiko
        print("command:", cmd)
        stdin, stdout, stderr = sshc.exec_command(cmd)
        print("stdout:")
        for line in stdout:
            print(line.strip("\n"))
        print("stderr:")
        for line in stderr:
            print(line.strip("\n"))

        # scp -i "web_app.pem" ubuntu@34.214.237.144:/home/ubuntu/result_img ./result_img
        with scp.SCPClient(sshc.get_transport()) as scpc:
            scpc.get(scp_trg, recursive=True)

        # Some weird GB stuff: https://github.com/paramiko/paramiko/issues/1078#issuecomment-596771584
        sshc.close()
        del sshc, stdin, stdout, stderr

    # Terminate the instance
    print("Try to terminate the instance")
    instance.terminate()

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
                                             instance_type=args.instance_type,
                                             ssh_key=args.ssh_key,
                                             scp_trg=args.scp_trg)
    print("instance_id: {}, public_ip: {}".format(instance_id, public_ip))

