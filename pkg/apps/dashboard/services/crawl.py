from django.conf import settings
from ..wrappers import role_wrapper, policy_wrapper, bucket_wrapper, glue_wrapper
import time


def get_s3_policy_doc(bucket_name):
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["glue:*"],
                "Resource": [
                    "arn:aws:glue:"+settings.REGION+":"+settings.ACCOUNT_NUMBER+":catalog",
                    "arn:aws:glue:"+settings.REGION+":"+settings.ACCOUNT_NUMBER+":database/*",
                    "arn:aws:glue:"+settings.REGION+":"+settings.ACCOUNT_NUMBER+":table/*"
                ],
            },
            {
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": [
                    "arn:aws:glue:"+settings.REGION+":"+settings.ACCOUNT_NUMBER+":log-group:/aws-glue/crawlers*",
                    "arn:aws:logs:*:*:/aws-glue/*",
                    "arn:aws:logs:*:*:/customlogs/*"
                ],
                "Effect": "Allow",
                "Sid": "ReadlogResources"
            },
            {
                "Action": [
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:PutBucketLogging",
                    "s3:ListBucket",
                    "s3:PutBucketVersioning"
                ],
                "Resource": [
                    "arn:aws:s3:::"+bucket_name+"",
                    "arn:aws:s3:::"+bucket_name+"/*"
                ],
                "Effect": "Allow",
                "Sid": "ReadS3Resources"
            }
        ]
    }
    return policy_doc


def get_snowflake_policy_doc(account_id, db_name, warehouse):
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "snowflake:Get*",
                    "snowflake:Describe*",
                    "snowflake:List*"
                ],
                "Resource": f"arn:aws:snowflake:us-west-2:123456789012:account/{account_id}"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "snowflake:Use*"
                ],
                "Resource": [
                    f"arn:aws:snowflake:us-west-2:123456789012:database/{db_name}/*",
                    f"arn:aws:snowflake:us-west-2:123456789012:warehouse/{warehouse}/*"
                ]
            }
        ]
    }
    return policy_doc


def get_rds_policy_doc(instance_id, username):
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "rds:DescribeDBInstances",
                    "rds:ListTagsForResource",
                    "rds:CreateDBSnapshot",
                    "rds:DeleteDBSnapshot",
                    "rds:RestoreDBInstanceFromDBSnapshot",
                    "rds:CreateDBInstance",
                    "rds:DeleteDBInstance",
                    "rds:ModifyDBInstance",
                    "rds:ModifyDBSnapshot",
                    "rds:RebootDBInstance",
                    "rds:PromoteReadReplica",
                    "rds:StartDBInstance",
                    "rds:StopDBInstance"
                ],
                "Resource": f"arn:aws:rds:us-east-1:123456789012:db:{instance_id}"
            },
            {
                "Effect": "Allow",
                "Action": "rds:Connect",
                "Resource": f"arn:aws:rds:us-east-1:123456789012:dbuser:{instance_id}/{username}"
            }
        ]
    }
    return policy_doc

def get_redshift_policy_doc():
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "redshift:DescribeClusters",
                    "redshift:CreateCluster",
                    "redshift:ModifyCluster",
                    "redshift:DeleteCluster",
                    "redshift:RestoreFromClusterSnapshot",
                    "redshift:RestoreTableFromClusterSnapshot",
                    "redshift:AuthorizeClusterSecurityGroupIngress",
                    "redshift:RevokeClusterSecurityGroupIngress",
                    "redshift:AuthorizeSnapshotAccess",
                    "redshift:CreateClusterSnapshot",
                    "redshift:DeleteClusterSnapshot",
                    "redshift:CreateClusterParameterGroup",
                    "redshift:DeleteClusterParameterGroup",
                    "redshift:DescribeClusterParameters",
                    "redshift:DescribeClusterSnapshots",
                    "redshift:DescribeClusterSecurityGroups",
                    "redshift:DescribeClusterParameterGroups",
                    "redshift:DescribeClusters",
                    "redshift:DescribeDefaultClusterParameters",
                    "redshift:DescribeEventCategories",
                    "redshift:DescribeEvents",
                    "redshift:DescribeEventSubscriptions",
                    "redshift:DescribeHsmConfigurations",
                    "redshift:DescribeLoggingStatus",
                    "redshift:DescribeOrderableClusterOptions",
                    "redshift:DescribeReservedNodeOfferings",
                    "redshift:DescribeReservedNodes",
                    "redshift:ModifyClusterIamRoles",
                    "redshift:ModifyClusterParameterGroup",
                    "redshift:ModifyClusterSubnetGroup",
                    "redshift:ModifyEventSubscription",
                    "redshift:ModifySnapshotCopyRetentionPeriod",
                    "redshift:RebootCluster",
                    "redshift:ResetClusterParameterGroup",
                    "redshift:RotateEncryptionKey",
                    "redshift:EnableLogging",
                    "redshift:DisableLogging",
                    "redshift:PurchaseReservedNodeOffering"
                ],
                "Resource": "*"
            }
        ]
    }
    return policy_doc


def get_jdbc_policy_doc(jdbc_secret_id):
    """
    param jdbc_secret_id: ARN of the secret containing JDBC connection credentials.
    """
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                    "secretsmanager:ListSecretVersionIds"
                ],
                "Resource": f"arn:aws:secretsmanager:us-east-1:123456789012:secret:{jdbc_secret_id}"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "glue:StartCrawler",
                    "glue:GetCrawler",
                    "glue:CreateCrawler",
                    "glue:DeleteCrawler",
                    "glue:UpdateCrawler",
                    "glue:ListCrawlers",
                    "glue:GetCrawlerMetrics",
                    "glue:GetDatabase",
                    "glue:CreateDatabase",
                    "glue:DeleteDatabase",
                    "glue:GetTable",
                    "glue:CreateTable",
                    "glue:DeleteTable",
                    "glue:GetConnection",
                    "glue:GetConnections",
                    "glue:GetTableVersions",
                    "glue:GetDatabases",
                    "glue:GetTableVersions",
                    "glue:BatchDeleteTableVersion",
                    "glue:CreateConnection"
                ],
                "Resource": "*"
            }
        ]
    }
    return policy_doc


def create_policy(name, self.target_type):
    policy_desc = f"This is {self.target_type} policy"
    if self.target_type == "jdbc":
        pass
    elif self.target_type == "s3":
        s3_resource = boto3.resource('s3')
        bucket = bucket_wrapper.BucketWrapper(s3_resource.Bucket(settings.BUCKET_NAME)
        if not bucket.exists():
            bucket.create()
        policy_doc = get_s3_policy_doc()
    
    policy = policy_wrapper.create_policy(name, policy_desc, policy_doc)
    return policy


class GlueIngestion:
    def __init__(self, identifier, target_type="jdbc", target_path=None):
        self.identifier = identifier
        self.target_type = target_type
        self.target_path = target_path
        self.role_name = settings.ROLE_NAME # AWSGlueServiceRole-custom
        self.glue_db_name = f"{self.identifier}-db"
        self.glue_crawler_name = f"{self.identifier}-crawler"
        
    @classmethod
    def extract_bucket_name(cls, target_path):
        match = re.match(r"s3://([^/]+)/", target_path)
        if match:
            return match.group(1)
        else:
            raise ValueError("Invalid S3 ingestion path")
        
    def get_iam_role(self):
        try:
            role = role_wrapper.get_role(self.role_name)
            policies = role_wrapper.list_attached_policies(self.role_name)
            if self.target_type == "jdbc":
                policy_name = f"{self.identifier}-jdbc-policy" # make the policy name unique for each instance
                if not policy_name in [policy.name for policy in policies]:
                    """
                    This applies if i could compare with policy.name 
                    if not i have to 
                    - try getting the policy if it exists, then compare with policy.arn
                    - if not, then i create the policy and attach it to the role 
                    """
                    policy = create_policy(policy_name, self.target_type)
                    role_wrapper.attach_policy(self.role_name, policy.arn)
            elif self.target_type == "s3":
                policy_name = f"{self.identifier}-{settings.BUCKET_NAME}-policy"
                if not policy_name in [policy.name for policy in policies]:
                    policy = create_policy(policy_name, self.target_type)
                    role_wrapper.attach_policy(self.role_name, policy.arn)
        except:
            role = role_wrapper.create_role(self.role_name)
            if self.target_type == "jdbc":
                policy_name = f"{self.identifier}-jdbc-policy" # make the policy name unique for each instance
                policy = create_policy(policy_name, self.target_type)
                
                role_wrapper.attach_policy(self.role_name, policy.arn)
                
            elif self.target_type == "s3":
                policy_name = f"{self.identifier}-{settings.BUCKET_NAME}-policy"
                policy = create_policy(policy_name, self.target_type)
                
                role_wrapper.attach_policy(self.role_name, policy.arn)
                
        return role
    
    def main(self):
        self.bucket_name = self.extract_bucket_name(self.target_path)
        
        role = self.get_iam_role()
        
        glue_client = boto3.client(
            'glue',
            aws_access_key_id=settings.DEV_ACCESS_KEY,
            aws_secret_access_key=settings.DEV_SECRET_KEY,
            region_name=settings.DEV_REGION,
        )
        
        glue = glue_wrapper.GlueWrapper(glue_client)
        glue.create_database(self.glue_db_name)
        
        if self.target_type == "s3":
            target = {'S3Targets': [
                {'Path': self.target_path}
            ]}
        elif self.target_type == "jdbc":
            target = {"JdbcTargets": [
                {"Path": self.target_path}
            ]}
        elif self.target_type == "mongodb":
            target = {"MongoDBTargets": [{
                "Path": self.target_path,
                "ScanAll": "false"
            }]}
        elif self.target_type == "dynamodb":
            target = {"DynamoDBTargets": [{
                "Path": self.target_path,
                "ScanAll": "false"
            }]}
        elif self.target_type == "delta":
            target = {"DeltaTargets": [{
                "DeltaTables": [], # A list of the Amazon S3 paths to the Delta tables.
            }]}
        elif self.target_type == "iceberg":
            target = {"IcebergTargets": [{
                "Paths": [], # One or more Amazon S3 paths that contains Iceberg metadata folders as s3://bucket/prefix.
            }]}
        elif self.target_type == "hudi":
            target = {"IcebergTargets": [{
                "Paths": [], # An array of Amazon S3 location strings for Hudi, each indicating the root folder with which the metadata files for a Hudi table resides.
            }]}
        
        glue.create_crawler(
            self.glue_crawler_name, 
            role.arn, 
            self.identifier, 
            self.glue_db_name, 
            target
        )
        
        glue.start_crawler(self.glue_crawler_name)
        
        while True:
            response = client.get_crawler(Name=glue_crawler_name)
             # Extract the crawler state
            status = response['Crawler']['State']
            # Print the crawler status
            print(f"Crawler '{glue_crawler_name}' status: {status}")
            if status == 'READY':  # Replace 'READY' with the desired completed state
                break  # Exit the loop if the desired state is reached
    
            time.sleep(5)  # Sleep for 10 seconds before checking the status again
        
        