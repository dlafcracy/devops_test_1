# Simple README and Notes

1. The base of this project is from AWS SAM python 3.7 Hello World Example template.

2. Dependency to do local development on MacOS:
- install brew
- install Docker CE Desktop
- brew tap aws/tap
- brew install aws-sam-cli

3. test lambda function with single sample event :
- sam local invoke HelloWorldFunction --event events/<test event json file>

4. list of test events :
- api_bad_event1.json (PUT request with empty body)
- api_bad_event2.json (DELETE request)
- api_bad_event3.json (request with no HTTP Request method)
- api_bad_event4.json (PUT request with username containing non-letters)
- api_bad_event5.json (PUT request with no body data)
- api_bad_event6.json (PUT request with invalid json format body data)
- api_bad_event7.json (PUT request with invalid date format body data)
- api_bad_event8.json (PUT request with future date, date from year 2222)
- api_good_event1.json (PUT request with valid date 31st december)
- api_good_event2.json (GET request with username 'username')
- api_good_event3.json (PUT request with valid date 1st january)
- api_good_event4.json (PUT request with no date but to be customized in automated test)

5. start local dev db : (in a separate terminal)
- docker-compose up

6. stop local dev db : (in the same separate terminal that started local dev db)
- Ctrl + C on terminal
- docker-compose down

7. extra packages are required to be compiled based on Amazon Linux 2 before using.
Note on Dockerfile used to build python 3.7 image.
Can leverage to download python packages as necessary.
https://github.com/lambci/docker-lambda/blob/master/python3.7/build/Dockerfile

8. depending on breaking changes across versions of application, there's 2 ways to be used for deployment of lambda as mentioned below. For this test app, Linear10PercentEvery1Minute traffic shifting is used.
https://github.com/awslabs/serverless-application-model/blob/master/docs/safe_lambda_deployments.rst

9. RDS setup using parameters from cloudformation template, inside SAM template.yaml
https://s3-us-west-2.amazonaws.com/cloudformation-templates-us-west-2/Drupal_Single_Instance_With_RDS.template

10. to run unit tests with pytest
- pip install pymysql cryptography pytest-docker
- DB_SERVER_HOST="127.0.0.1" python -m pytest tests/ -v
or
- pip3 install pymysql cryptography pytest-docker --user (on mac with python3 installed)
- DB_SERVER_HOST="127.0.0.1" python3 -m pytest tests/ -v

11. db configuration can be externalized as api_config.py.

12. to deploy to AWS (this will include auto detect changeset required)
- aws configure (run one time to setup AWS cli credentials)
- sam build --use-container
- sam deploy --guided
- note* :
  - This sam template covers setup of Lambda function, API gateway and RDS Aurora DB initialization.
  - RDS actual database endpoint will only appear after Cloudformation stack deployment is complete .
  - After that, need to go to AWS lambda console to change environment variable "DB_SERVER_HOST" for lambda function to allow connection to RDS.
  - This works on the assumption there is not VPC setup yet. Otherwise more configuration is needed in template.yml to include setup for VPC, subnets, Security group, Network ACL, Routing Table, VPC Endpoint for AWS Lambda, AWS Route53, AWS WAF enabling at API Gateway.
  - Custom domain name can be used here to alias to any specific url on API gateway. https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-custom-domain-names.html
