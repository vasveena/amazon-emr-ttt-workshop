#!/bin/bash

set -xve
CFTS3Bucket=$1

sudo aws s3 cp s3://aws-bigdata-blog/artifacts/hudiblog/configs/dfs-source-retail-transactions-full.properties /home/hadoop/
sudo aws s3 cp s3://aws-bigdata-blog/artifacts/hudiblog/configs/dfs-source-retail-transactions-incremental.properties /home/hadoop/
sudo aws s3 cp s3://aws-bigdata-blog/artifacts/hudiblog/configs/base.properties s3://"${CFTS3Bucket}"/properties/

sudo chmod a+rw /home/hadoop/dfs-source-retail-transactions-full.properties
sudo chmod a+rw /home/hadoop/dfs-source-retail-transactions-incremental.properties


sudo yum install -y jq

#export CLUSTER_ID=`aws emr list-clusters --active | jq -r '.[] | .[] | select(.Name=="hudiblogemrcluster") | .Id'`
export CLUSTER_ID=`cat /emr/instance-controller/lib/info/extraInstanceData.json | jq '.jobFlowId' | sed 's/"//g'`
export MASTER_DNS=`aws emr describe-cluster --cluster-id $CLUSTER_ID | jq -r   '.[].MasterPublicDnsName'`
export PRIVATE_IP=`aws emr list-instances --cluster-id $CLUSTER_ID --instance-group-types MASTER | jq -r   '.[] |.[].PrivateIpAddress'`

echo "hoodie.deltastreamer.source.dfs.root=s3://"${CFTS3Bucket}"/dmsdata/data-full/dev/retail_transactions" >> /home/hadoop/dfs-source-retail-transactions-full.properties
echo "hoodie.deltastreamer.source.dfs.root=s3://"${CFTS3Bucket}"/dmsdata/dev/retail_transactions" >> /home/hadoop/dfs-source-retail-transactions-incremental.properties
echo "hoodie.deltastreamer.schemaprovider.source.schema.file=s3://"${CFTS3Bucket}"/schema/source-full.avsc" >>/home/hadoop/dfs-source-retail-transactions-full.properties
echo "hoodie.deltastreamer.schemaprovider.source.schema.file=s3://"${CFTS3Bucket}"/schema/source-incremental.avsc" >>/home/hadoop/dfs-source-retail-transactions-incremental.properties
echo "hoodie.deltastreamer.schemaprovider.target.schema.file=s3://"${CFTS3Bucket}"/schema/target.avsc" >>/home/hadoop/dfs-source-retail-transactions-full.properties
echo "hoodie.deltastreamer.schemaprovider.target.schema.file=s3://"${CFTS3Bucket}"/schema/target.avsc" >>/home/hadoop/dfs-source-retail-transactions-incremental.properties
echo "hoodie.datasource.hive_sync.jdbcurl=jdbc:hive2://"${PRIVATE_IP}":10000" >>/home/hadoop/dfs-source-retail-transactions-full.properties
echo "hoodie.datasource.hive_sync.jdbcurl=jdbc:hive2://"${PRIVATE_IP}":10000" >>/home/hadoop/dfs-source-retail-transactions-incremental.properties
echo "include=s3://"${CFTS3Bucket}"/properties/base.properties" >>/home/hadoop/dfs-source-retail-transactions-full.properties
echo "include=s3://"${CFTS3Bucket}"/properties/base.properties" >>/home/hadoop/dfs-source-retail-transactions-incremental.properties

aws s3 cp s3://aws-bigdata-blog/artifacts/hudiblog/schema/source-full.avsc s3://"${CFTS3Bucket}"/schema/
aws s3 cp s3://aws-bigdata-blog/artifacts/hudiblog/schema/source-incremental.avsc s3://"${CFTS3Bucket}"/schema/
aws s3 cp s3://aws-bigdata-blog/artifacts/hudiblog/schema/target.avsc s3://"${CFTS3Bucket}"/schema/

aws s3 cp /home/hadoop/dfs-source-retail-transactions-full.properties s3://"${CFTS3Bucket}"/properties/
aws s3 cp /home/hadoop/dfs-source-retail-transactions-incremental.properties s3://"${CFTS3Bucket}"/properties/
#sudo yum install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm	
#sudo start amazon-ssm-agent

echo "Bootstrap completed successfully"
exit 0


