import boto3
from botocore.exceptions import ClientError

regions = [x['RegionName'] for x in boto3.client("ec2").describe_regions()['Regions']]

# regions = ['cn-northwest-1', 'cn-north-1']
ec2_name_tags = {}


def ec2():
    for region in regions:
        ec2client = boto3.client("ec2", region_name=region)
        instance_description_result = ec2client.describe_instances()
        for reservation in instance_description_result['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                ec2client.create_tags(Resources=[instance_id], Tags=[{'Key': 'Service', 'Value': 'AmazonEC2'}])
                print("[EC2:TAGGING-OK] " + instance_id)
                instance_name_tag = ''
                for instance_tag in instance['Tags']:
                    if instance_tag['Key'] == 'Name':
                        instance_name_tag = instance_tag['Value']
                        ec2_name_tags[instance_id] = instance_name_tag
                for block_device in instance['BlockDeviceMappings']:
                    volume_id = block_device['Ebs']['VolumeId']
                    ec2client.create_tags(Resources=[volume_id], Tags=[
                        {'Key': 'Service', 'Value': 'AmazonEC2'},
                        {'Key': 'Name', 'Value': instance_name_tag},
                    ])
                    print("[EC2-EBS:TAGGING-OK] " + volume_id)
        addresses = ec2client.describe_addresses()['Addresses']
        for address in addresses:
            address_allocation_id = address['AllocationId']
            if address.__contains__("InstanceId"):
                applied_ec2_instance_name = ec2_name_tags[address['InstanceId']]
                ec2client.create_tags(Resources=[address_allocation_id], Tags=[{'Key': 'Service', 'Value': 'AmazonEC2'},
                                                                               {'Key': 'Name',
                                                                                'Value': applied_ec2_instance_name}])
            else:
                ec2client.create_tags(Resources=[address_allocation_id],
                                      Tags=[{'Key': 'Service', 'Value': 'AmazonEC2'}])
            print("[EC2-EIP:TAGGING-OK] " + address_allocation_id)


def rds():
    for region in regions:
        rds_client = boto3.client("rds", region_name=region)
        result = rds_client.describe_db_instances()
        rds_db_instance_list = result['DBInstances']
        for rds_db_instance in rds_db_instance_list:
            db_instance_arn = rds_db_instance['DBInstanceArn']
            db_instance_identifier = rds_db_instance['DBInstanceIdentifier']
            rds_client.add_tags_to_resource(
                ResourceName=db_instance_arn,
                Tags=[
                    {'Key': 'Name', 'Value': db_instance_identifier},
                    {'Key': 'Service', 'Value': 'AmazonRDS'},
                ]
            )
            print("[RDS:TAGGING-OK] " + db_instance_identifier)


def s3():
    s3client = boto3.client("s3")
    result = s3client.list_buckets()
    s3_bucket_list = result['Buckets']
    for s3_bucket in s3_bucket_list:
        bucket_name = s3_bucket['Name']
        print(bucket_name)
        tags_map = {}
        try:
            tags_result = s3client.get_bucket_tagging(Bucket=bucket_name)
            tags = tags_result['TagSet']
            for tag in tags:
                tags_map[tag['Key']] = tag['Value']
        except ClientError as clientError:
            # print(clientError)
            pass

        tags_map['Name'] = bucket_name
        tags_map['Service'] = 'AmazonS3'

        tag_set_to_put = []
        for key in tags_map.keys():
            tag_set_to_put.append({
                'Key': key,
                'Value': tags_map[key]
            })

        try:
            s3client.put_bucket_tagging(
                Bucket=bucket_name,
                Tagging={
                    "TagSet": tag_set_to_put
                }
            )

        except ClientError as clientError:
            print("Put bucket tagging ERROR.")
        print(tag_set_to_put)
        print("==================")


def awslambda():
    for region in regions:
        awslambdaclient = boto3.client("lambda", region_name=region)
        functions = awslambdaclient.list_functions()['Functions']
        for function in functions:
            function_name = function['FunctionName']
            function_arn = function['FunctionArn']
            awslambdaclient.tag_resource(
                Resource=function_arn,
                Tags={
                    "Name": function_name,
                    "Service": 'AWSLambda'
                }
            )
            print("[LAMBDA:TAGGING-OK] " + function_name)


def sqs():
    for region in regions:
        sqsclient = boto3.client("sqs", region_name=region)
        list_queues_result = sqsclient.list_queues()
        queue_urls = list_queues_result['QueueUrls'] if list_queues_result.__contains__("QueueUrls") else []
        for queue_url in queue_urls:
            queue_name = queue_url.split("/")[-1]
            sqsclient.tag_queue(QueueUrl=queue_url, Tags={
                "Name": queue_name,
                "Service": "AmazonSQS"
            })
            print("[SQS:TAGGING-OK] " + queue_url)


if __name__ == '__main__':
    ec2()
    rds()
    s3()
    awslambda()
    sqs()
