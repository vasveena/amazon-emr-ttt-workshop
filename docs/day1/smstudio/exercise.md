# ** Exercise 4 - Sagemaker Studio Integration with Amazon EMR **

### Create a new Sagemaker Studio

Go to the Amazon Sagemaker Web Console -> Get started -> Sagemaker Studio

![sm - 7](images/sm-7.png)

Under User profile, leave Name defaulted. For Default execution role, choose "Create New Role". Choose "Any S3 Bucket". Create role.

![sm - 9](images/sm-9.png)

Submit. You will now be prompted to select a VPC. Choose the "MMVPC" from the options. For subnet, choose "MMPublicSubnetOne". Save and continue.

![sm - 8](images/sm-8.png)

Wait for the Sagemaker domain is ready (it will take about 3-4 mins). Once the Sagemaker domain is ready, launch the Sagemaker Studio from Launch app -> Studio.

![sm - 10](images/sm-10.png)

It will take about 2 minutes to initialize after which you will be taken to the Sagemaker Studio interface.

![sm - 11](images/sm-11.png)

Once you are in, carry on with rest of the steps.

![sm - 12](images/sm-12.png)

### Explore EMR clusters in Sagemaker Studio

Click on the ![sm - 1](images/sm-1.png) icon and choose Clusters from the Sagemaker resources drop down. You will be able to see the EMR clusters.

![sm - 2](images/sm-2.png)

You can filter the EMR clusters and also create a new one with a cluster template created from AWS Service Catalog. For this time, we will use an existing cluster.

### Connect to EMR cluster from Sagemaker Studio and run data processing jobs

Go to Git repository section and click on Clone the repository.

![sm - 3](images/sm-3.png)

Specify the repository to clone: https://github.com/vasveena/amazon-emr-ttt-workshop.git

Make sure that the repository is cloned.

![sm - 4](images/sm-4.png)

Go to Files section (folder icon on the left hand side pane).

![sm - 5](images/sm-5.png)

Go to the directory files -> notebook -> smstudio-pyspark-hive-sentiment-analysis.ipynb. Choose the SparkMagic Kernel when prompted and click "Select".

![sm - 6](images/sm-6.png)

It will take a minute or so for the kernel to initialize. Now, you can run the code blocks of the notebook. In the ln[2], uncomment the code block and replace j-xxxxxxxxxxxx with the cluster ID of "EMR-Spark-Hive-Presto" EMR cluster (obtained from EMR Web Console -> EMR-Spark-Hive-Presto -> Summary tab).
