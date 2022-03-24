# **Apache Hive and Presto on EMR**

In this section we are going to use Hive and Presto to run batch ETL jobs and adhoc queries.

### Hive on EMR

#### Running Hive jobs on Hue

In AWS Web Console, Go to EMR Console -> EMR-Hive-HBaseOnS3

![hv - 1](images/hv-1.png)

Login to the leader node of this cluster using Session Manager or SSH (Go to Hardware tab -> master fleet -> Click on the instance ID -> Go to EC2 console -> Connect with Session Manager). Run the following command:

```
cd ~
sudo su hadoop
sudo -su hdfs hdfs dfs -chmod -R 777 /

```

Let's connect to Hue in this cluster to submit Hive queries. For this you will need to install [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and [Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html) on your local desktop to do this.

Replace the environmental variables with the values from the Team Dashboard. Run the below commands in your local desktop. For Windows, you will need to use "set" instead of "export".

![hv - 2](images/hv-2.png)

```
export AWS_DEFAULT_REGION=us-east-1
export AWS_ACCESS_KEY_ID=<redacted>
export AWS_SECRET_ACCESS_KEY=<redacted>
export AWS_SESSION_TOKEN=<redacted>

```

Run the below command on your local desktop. Replace --target with your leader node instance ID of the EMR cluster in the following command.

```
aws ssm start-session --target i-054c79edd2456227b --document-name AWS-StartPortForwardingSession --parameters '{"portNumber":["8888"], "localPortNumber":["8158"]}' --region us-east-1

```

![hv - 3](images/hv-3.png)

It should start a session on Hue port (8888). Go to the your browser and type *http://localhost:8158* in the address bar. You should now be taken to the Hue console.

![hv - 4](images/hv-4.png)

Login to Hue by. You can choose any user name and password you like. Click "Create account". Once you are logged in, you will see Hue editor.

![hv - 5](images/hv-5.png)

By default, it goes to MySQL editor. Click on this icon ![hv - 6](images/hv-6.png) on the top left corner and choose Hive editor.

![hv - 7](images/hv-7.png)

Now we can run some Hive queries. Copy the below contents into Hue editor. Run these queries on Hue one at a time. REPLACE your account ID in S3 location wherever instructed.

```
CREATE TABLE `lineitem`(
  `l_orderkey` string,
  `l_partkey` bigint,
  `l_suppkey` string,
  `l_linenumber` bigint,
  `l_quantity` bigint,
  `l_extendedprice` double,
  `l_discount` double,
  `l_tax` double,
  `l_returnflag` string,
  `l_linestatus` string,
  `l_shipdate` string,
  `l_commitdate` string,
  `l_receiptdate` string,
  `l_shipinstruct` string,
  `l_shipmode` string,
  `l_comment` string)
ROW FORMAT DELIMITED
  FIELDS TERMINATED BY '|'
STORED AS INPUTFORMAT
  'org.apache.hadoop.mapred.TextInputFormat'
OUTPUTFORMAT
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://redshift-downloads/TPC-H/10GB/lineitem/';


  CREATE EXTERNAL TABLE `orders`(
    `o_orderkey` bigint,
    `o_custkey` bigint,
    `o_orderstatus` string,
    `o_totalprice` double,
    `o_orderdate` string,
    `o_orderpriority` string,
    `o_clerk` string,
    `o_shippriority` bigint,
    `o_comment` string)
  ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '|'
  STORED AS INPUTFORMAT
    'org.apache.hadoop.mapred.TextInputFormat'
  OUTPUTFORMAT
    'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
  LOCATION
    's3://redshift-downloads/TPC-H/10GB/orders/';

  -- REPLACE your account ID in S3 location

CREATE EXTERNAL TABLE `lineitemorders`(
  `orderkey` string,
  `linenumber` bigint,
  `quantity` bigint,
  `totalprice` double,
  `extendedprice` double,
  `tax` double,
  `discount` double,
  `orderpriority` string,
  `shippriority` bigint)
PARTITIONED BY (linestatus string)
CLUSTERED BY (orderkey)
SORTED BY (orderkey ASC)
INTO 10 BUCKETS
STORED AS PARQUET
LOCATION 's3://mrworkshop-youraccountID-dayone/hive/lineitemorders/';

set hive.exec.dynamic.partition=true;  
set hive.exec.dynamic.partition.mode=nonstrict;

insert overwrite table lineitemorders
partition (linestatus = 'O')
select o_orderkey,
l_linenumber
l_quantity,
o_totalprice,
l_extendedprice,
l_tax,
l_discount,
o_orderpriority,
o_shippriority,
o_orderdate as orderdate
from lineitem join orders
on l_orderkey = o_orderkey
where l_linestatus = 'O';

select * from lineitemorders limit 5;


select quantity * (totalprice + extendedprice) as finalprice, orderpriority
from lineitemorders
where linestatus = 'O'
group by orderpriority, quantity, totalprice, extendedprice, tax, discount
order by 1 desc
limit 5;

```

#### Hive ACID tables

Hive supports ACID tables. A single statement can write to multiple partitions or multiple tables. If the operation fails, partial writes or inserts are not visible to users. Operations remain performant even if data changes often, such as one percent per hour. Does not overwrite the entire partition to perform update or delete operations.

Run the below commands in Hue editor one by one. Replace youraccountID with your AWS event engine account ID.

```
set hive.support.concurrency=true;
set hive.exec.dynamic.partition.mode=nonstrict;
set hive.txn.manager=org.apache.hadoop.hive.ql.lockmgr.DbTxnManager;

--REPLACE your account in the S3 location

CREATE TABLE acid_tbl
(
  key INT,
  value STRING,
  action STRING
)
CLUSTERED BY (key) INTO 3 BUCKETS
STORED AS ORC
LOCATION 's3://mrworkshop-youraccountID-dayone/hive/acid_tbl'
TBLPROPERTIES ('transactional'='true');

INSERT INTO acid_tbl VALUES
(1, 'val1', 'insert'),
(2, 'val2', 'insert'),
(3, 'val3', 'insert'),
(4, 'val4', 'insert'),
(5, 'val5', 'insert');

SELECT * FROM acid_tbl;

UPDATE acid_tbl SET value = 'val5_1', action = 'update' WHERE key = 5;
SELECT * FROM acid_tbl;

DELETE FROM acid_tbl WHERE key = 4;
SELECT * FROM acid_tbl;

DROP TABLE IF EXISTS acid_merge;
CREATE TABLE acid_merge
(
  key INT,
  new_value STRING
)
STORED AS ORC;

INSERT INTO acid_merge VALUES
(1, 'val1_1'),
(3, NULL),
(6, 'val6');

MERGE INTO acid_tbl AS T
USING acid_merge AS M
ON T.key = M.key
WHEN MATCHED AND M.new_value IS NOT NULL
  THEN UPDATE SET value = M.new_value, action = 'merge_update'
WHEN MATCHED AND M.new_value IS NULL
  THEN DELETE
WHEN NOT MATCHED
  THEN INSERT VALUES (M.key, M.new_value, 'merge_insert');

SELECT * FROM acid_tbl;

ALTER TABLE acid_tbl COMPACT 'minor';
SHOW COMPACTIONS;

SET hive.compactor.check.interval;

ALTER TABLE acid_tbl COMPACT 'major';
show compactions;

select row__id, key, value, action from acid_tbl;

```

#### Orchestrate Hive jobs with AWS Step Functions

Simba provides [JDBC drivers](https://docs.aws.amazon.com/emr/latest/ReleaseGuide/HiveJDBCDriver.html) for Hive and Presto to connect from BI tools like Tableau or SQL Workbench.

Please note you can use AWS Step Functions to orchestrate any kind of EMR steps. But we are just using Hive steps here as an example.

Go to AWS Management Console -> AWS Step Functions -> Create State Machine.

Choose middle option “Write your own workflow in code”. Under “Definition” enter the following code block.

Edit InstanceProfile Role and account ID in below code (marked as CHANGEME). Use the instance profile being used by your "EMR-Spark-Hive-Presto" cluster. It will look like "dayone-emrEc2InstanceProfile-XXXXXXX". This information can be retrieved from the Summary tab of your EMR cluster. (EMR Web Console -> EMR-Spark-Hive-Presto -> EC2 instance profile under Security Access). Change your account ID in the S3 bucket names.

```

{
  "StartAt": "Should_Create_Cluster",
  "States": {
    "Should_Create_Cluster": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.CreateCluster",
          "BooleanEquals": true,
          "Next": "Create_A_Cluster"
        },
        {
          "Variable": "$.CreateCluster",
          "BooleanEquals": false,
          "Next": "Enable_Termination_Protection"
        }
      ],
      "Default": "Create_A_Cluster"
    },
    "Create_A_Cluster": {
      "Type": "Task",
      "Resource": "arn:aws:states:::elasticmapreduce:createCluster.sync",
      "Parameters": {
        "Name": "WorkflowCluster",
        "VisibleToAllUsers": true,
        "ReleaseLabel": "emr-5.28.0",
        "Applications": [{ "Name": "Hive" }],
        "ServiceRole": "emrServiceRole",
        "JobFlowRole": "CHANGEME",
        "Instances": {
          "KeepJobFlowAliveWhenNoSteps": true,
          "InstanceFleets": [
            {
              "InstanceFleetType": "MASTER",
              "TargetOnDemandCapacity": 1,
              "InstanceTypeConfigs": [
                {
                  "InstanceType": "m4.xlarge"
                }
              ]
            },
            {
              "InstanceFleetType": "CORE",
              "TargetOnDemandCapacity": 1,
              "InstanceTypeConfigs": [
                {
                  "InstanceType": "m4.xlarge"
                }
              ]
            }
          ]
        }
      },
      "ResultPath": "$.CreateClusterResult",
      "Next": "Merge_Results"
    },
    "Merge_Results": {
      "Type": "Pass",
      "Parameters": {
        "CreateCluster.$": "$.CreateCluster",
        "TerminateCluster.$": "$.TerminateCluster",
        "ClusterId.$": "$.CreateClusterResult.ClusterId"
      },
      "Next": "Enable_Termination_Protection"
    },
    "Enable_Termination_Protection": {
      "Type": "Task",
      "Resource": "arn:aws:states:::elasticmapreduce:setClusterTerminationProtection",
      "Parameters": {
        "ClusterId.$": "$.ClusterId",
        "TerminationProtected": true
      },
      "ResultPath": null,
      "Next": "Add_Steps_Parallel"
    },
    "Add_Steps_Parallel": {
      "Type": "Parallel",
      "Branches": [
        {
          "StartAt": "Step_One",
          "States": {
            "Step_One": {
              "Type": "Task",
              "Resource": "arn:aws:states:::elasticmapreduce:addStep.sync",
              "Parameters": {
                "ClusterId.$": "$.ClusterId",
                "Step": {
                  "Name": "The first step",
                  "ActionOnFailure": "CONTINUE",
                  "HadoopJarStep": {
                    "Jar": "command-runner.jar",
                    "Args": [
                      "hive-script",
                      "--run-hive-script",
                      "--args",
                      "-f",
                      "s3://eu-west-1.elasticmapreduce.samples/cloudfront/code/Hive_CloudFront.q",
                      "-d",
                      "INPUT=s3://eu-west-1.elasticmapreduce.samples",
                      "-d",
                      "OUTPUT=s3://mrworkshop-CHANGEME-dayone/MyHiveQueryResults/"
                    ]
                  }
                }
              },
              "End": true
            }
          }
        },
        {
          "StartAt": "Wait_10_Seconds",
          "States": {
            "Wait_10_Seconds": {
              "Type": "Wait",
              "Seconds": 10,
              "Next": "Step_Two (async)"
            },
            "Step_Two (async)": {
              "Type": "Task",
              "Resource": "arn:aws:states:::elasticmapreduce:addStep",
              "Parameters": {
                "ClusterId.$": "$.ClusterId",
                "Step": {
                  "Name": "The second step",
                  "ActionOnFailure": "CONTINUE",
                  "HadoopJarStep": {
                    "Jar": "command-runner.jar",
                    "Args": [
                      "hive-script",
                      "--run-hive-script",
                      "--args",
                      "-f",
                      "s3://eu-west-1.elasticmapreduce.samples/cloudfront/code/Hive_CloudFront.q",
                      "-d",
                      "INPUT=s3://eu-west-1.elasticmapreduce.samples",
                      "-d",
                      "OUTPUT=s3://mrworkshop-CHANGEME-dayone/MyHiveQueryResults/"
                    ]                  
                  }
                }
              },
              "ResultPath": "$.AddStepsResult",
              "Next": "Wait_Another_10_Seconds"
            },
            "Wait_Another_10_Seconds": {
              "Type": "Wait",
              "Seconds": 10,
              "Next": "Cancel_Step_Two"
            },
            "Cancel_Step_Two": {
              "Type": "Task",
              "Resource": "arn:aws:states:::elasticmapreduce:cancelStep",
              "Parameters": {
                "ClusterId.$": "$.ClusterId",
                "StepId.$": "$.AddStepsResult.StepId"
              },
              "End": true
            }
          }
        }
      ],
      "ResultPath": null,
      "Next": "Step_Three"
    },
    "Step_Three": {
      "Type": "Task",
      "Resource": "arn:aws:states:::elasticmapreduce:addStep.sync",
      "Parameters": {
        "ClusterId.$": "$.ClusterId",
        "Step": {
          "Name": "The third step",
          "ActionOnFailure": "CONTINUE",
          "HadoopJarStep": {
            "Jar": "command-runner.jar",
            "Args": [
                      "hive-script",
                      "--run-hive-script",
                      "--args",
                      "-f",
                      "s3://eu-west-1.elasticmapreduce.samples/cloudfront/code/Hive_CloudFront.q",
                      "-d",
                      "INPUT=s3://eu-west-1.elasticmapreduce.samples",
                      "-d",
                      "OUTPUT=s3://mrworkshop-CHANGEME-dayone/MyHiveQueryResults/"
             ]
          }
        }
      },
      "ResultPath": null,
      "Next": "Disable_Termination_Protection"
    },
    "Disable_Termination_Protection": {
      "Type": "Task",
      "Resource": "arn:aws:states:::elasticmapreduce:setClusterTerminationProtection",
      "Parameters": {
        "ClusterId.$": "$.ClusterId",
        "TerminationProtected": false
      },
      "ResultPath": null,
      "Next": "Should_Terminate_Cluster"
    },
    "Should_Terminate_Cluster": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.TerminateCluster",
          "BooleanEquals": true,
          "Next": "Terminate_Cluster"
        },
        {
          "Variable": "$.TerminateCluster",
          "BooleanEquals": false,
          "Next": "Wrapping_Up"
        }
      ],
      "Default": "Wrapping_Up"
    },
    "Terminate_Cluster": {
      "Type": "Task",
      "Resource": "arn:aws:states:::elasticmapreduce:terminateCluster.sync",
      "Parameters": {
        "ClusterId.$": "$.ClusterId"
      },
      "Next": "Wrapping_Up"
    },
    "Wrapping_Up": {
      "Type": "Pass",
      "End": true
    }
  }
}

```

Then, you can keep rest as default and create state machine.

After the state machine is created, click on “Start Execution” and enter the below JSON input.

```

{
  "CreateCluster": true,
  "TerminateCluster": true
}

```

Click on “Start Execution” and observe the workflow. You can see the “Workflow cluster” being created. It will run the EMR Hive steps as chained workflows. You can also use AWS Event Bridge to schedule jobs using AWS Step Functions.

### S3DistCp Utility

Hive is typically used for batch ETL transformations. Presto is used for adhoc/interactive querying.

For flat copy (copying files without applying any transformations), it is always better to use S3-Dist-Cp than using Hive insert overwrite queries. Before we use Hive and Presto for querying, lets use S3-Dist-Cp utility to migrate CSV data and convert it into Parquet format.

Run the below two commands on EMR leader node.

```
sudo su hadoop
cd ~

s3-dist-cp --src  s3://redshift-downloads/TPC-H/3TB/lineitem/ --dest /user/hadoop/lineitem
s3-dist-cp --src  s3://redshift-downloads/TPC-H/3TB/orders/ --dest /user/hadoop/orders

```
Now, lets
