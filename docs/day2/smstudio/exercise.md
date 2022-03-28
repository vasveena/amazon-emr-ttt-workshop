# **Sagemaker Studio Integration with Amazon EMR**

Amazon Sagemaker provides native integration with Amazon EMR from Sagemaker Studio so that you can run data preparation tasks for your machine learning workloads using EMR from Sagemaker.

### Login to the Sagemaker Studio

Go to the Amazon Sagemaker Web Console -> Get started -> Sagemaker Studio

![sm - 7](images/sm-7.png)

You should see the Sagemaker domain ready status. Launch the Sagemaker Studio from Launch app -> Studio.

![sm - 8](images/sm-8.png)

It will take about 2 minutes to initialize after which you will be taken to the Sagemaker Studio interface.

![sm - 11](images/sm-11.png)

Once you are in, carry on with rest of the steps.

![sm - 12](images/sm-12.png)

### Explore EMR clusters in Sagemaker Studio

Click on the ![sm - 1](images/sm-1.png) icon and choose Clusters from the Sagemaker resources drop down. You will be able to see the EMR clusters.

![sm - 2](images/sm-2.png)

You can filter the EMR clusters and also create a new one with a cluster template created from AWS Service Catalog. Go to Clusters -> Create cluster. You will be able to see a template.

![sm - 9](images/sm-9.png)

When you select the template, it will show you the blueprint for your EMR cluster creation.

![sm - 10](images/sm-10.png)

For now, let's use our existing cluster.

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

It will take a few minutes for the kernel to initialize. Once the kernel starts, go to Cluster on the top right corner and choose the EMR cluster "EMR-Spark-Hive-Presto". When it asks for credential type, choose "No credential" and Connect. Now, a Spark application will be created.

![sm - 14](images/sm-14.png)

Now, you can run the remaining code blocks of the notebook which will perform data transformations and explorations using the EMR cluster and create and host an ML model using Sagemaker.
