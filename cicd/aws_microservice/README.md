# Simple AWS CI/CD Pipeline

This is a CI/CD pipeline that deploys a simple flask microservice
into AWS Elastic Container Service behind a load balancer, tests
it, and then cleans up all AWS resources.

You must have an AWS account and specify the following as secrets
in the Conducto app:
* AWS_ACCESS_KEY_ID
* AWS_SECRET_ACCESS_KEY
* AWS_DEFAULT_REGION

Note that this pipeline allocates AWS resources that may incur a
charge while running. Do not forget to unskip and run the "Cleanup"
node when you are done to delete these AWS resources.