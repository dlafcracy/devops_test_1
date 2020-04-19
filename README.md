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
- api_good_event1.json

5. start local dev db : (in a separate terminal)
- docker-compose up

6. stop local dev db : (in the same separate terminal that started local dev db)
- Ctrl + C on terminal
- docker-compose down

7. extra packages are required to be compiled based on Amazon Linux 2 before using.
Note on Dockerfile used to build python 3.7 image.
Can leverage to download python packages as necessary.
https://github.com/lambci/docker-lambda/blob/master/python3.7/build/Dockerfile
