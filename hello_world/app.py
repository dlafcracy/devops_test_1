import json
import os
import logging
import datetime
import pymysql
import pymysql.cursors
import cryptography

# default configuration setup
api_context_path = os.getenv('API_CONTEXT_PATH') or '/hello/'
db_server_host = os.getenv('DB_SERVER_HOST') or 'docker.for.mac.localhost'
db_port = os.getenv('DB_PORT') or 3306
db_name = os.getenv('DB_NAME') or 'sam'
db_user_name = os.getenv('DB_USERNAME') or 'sam'
db_user_password = os.getenv('DB_PASSWORD') or 'sampassword1'

# setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# setup global variable
connection = None
cursor = None
# used to store response across function for get request
get_request_response_code = None
get_request_response_message = None

# validate incoming event request
def validate_http_request(event):
    tmp_http_method = None
    # error if httpMethod is not provided
    try:
        tmp_http_method = event["httpMethod"]
        http_method = tmp_http_method.upper()
        # error if httpMethod is not GET or PUT
        if http_method in ['GET', 'PUT']:
            logger.info('## Received ' + str(http_method) + ' request.')
        else:
            logger.error('** Bad HTTP Method.')
            return False
    except Exception as e:
        logger.error('** Missing HTTP Method.')
        return False

    # error if path is not provided
    try:
        http_url = event["path"]
        # error if path is not valid
        if http_url.startswith(api_context_path, 0):
            sub_http_url = http_url.replace(api_context_path, '', 1)
            # error if subpath (which is username) contain nonletters
            if sub_http_url.isalpha():
                logger.info('## Received request for username ' + str(sub_http_url) + '.')
            else:
                logger.error('** Bad username request.')
                return False
        else:
            logger.error('** Bad HTTP Request Path.')
            return False
    except Exception as e:
        logger.error('** Missing HTTP Request Path.')
        return False

    # check body data from PUT request
    if http_method == 'PUT':
        try:
            http_body = event["body"]
            json_http_body = json.loads(http_body)
            date_of_birth_str = json_http_body["dateOfBirth"]
            date_of_birth_obj = datetime.datetime.strptime(date_of_birth_str, '%Y-%m-%d')
            current_date_obj = datetime.datetime.now()
            if date_of_birth_obj.date() < current_date_obj.date():
                logger.info('## Received request with dateOfBirth ' + str(date_of_birth_obj.date()) + ' which is a date from the past.')
            else:
                logger.error('** Bad date for dateOfBirth in PUT request.')
                return False
        except Exception as e:
            logger.error('** Missing valid json formatted body data with valid date format for PUT request.')
            return False

    # passed all checks
    return True

# check database connection
def check_database_connection():
    global connection
    global cursor
    try:
        connection = pymysql.connect(host=db_server_host, user=db_user_name, passwd=db_user_password, db=db_name, port=db_port, connect_timeout=5)
        cursor = connection.cursor()
        logger.info('## Connected to DB.')
    except pymysql.MySQLError as e:
        logger.error("** Failed connection to DB.")
        logger.error(e)
        return False
    # mark database connection good
    return True

# list of database queries
check_record_sql = 'SELECT * FROM records WHERE UserName = "%%s"'
insert_record_sql = 'INSERT INTO records (UserName, DateOfBirth) VALUES ("%s", "%s")'
update_record_sql = 'UPDATE records SET DateOfBirth = "%s" WHERE UserName = "%s"'

# prepare database table
def prep_database():
    global connection
    global cursor
    try:
        with connection.cursor() as cursor:
            # check for table 'records' which will be used for storing data
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = '{0}'
                AND table_name = 'records'
            """.format(db_name))
            if cursor.rowcount < 1:
                try:
                    logger.info('## Creating table in DB.')
                    # force create table 'records' to store data
                    cursor.execute("""
                        CREATE TABLE records
                        ( ID int NOT NULL AUTO_INCREMENT,
                        UserName varchar(255) COLLATE utf8mb4_bin NOT NULL,
                        DateOfBirth varchar(255) COLLATE utf8mb4_bin NOT NULL,
                        PRIMARY KEY (ID) )
                        ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                        COLLATE=utf8mb4_bin AUTO_INCREMENT=1
                    """)
                    connection.commit()
                    logger.info('## Required table created. DB is ready to serve.')
                except pymysql.MySQLError as e:
                    logger.error("** Failed creating table in DB.")
                    logger.error(e)
                    return False
            else:
                logger.info('## Found required table. DB is ready to serve.')
    except pymysql.MySQLError as e:
        logger.error("** Failed preparing DB.")
        logger.error(e)
        return False
    # mark database ready
    return True

# insert or update data from PUT request
def update_record(username, dateofbirth):
    global connection
    global cursor
    try:
        with connection.cursor() as cursor:
            # check for record
            cursor.execute("""
                SELECT *
                FROM `records`
                WHERE UserName = '{0}'
            """.format(username))
            if cursor.rowcount < 1:
                logger.info('## Creating new record in DB.')
                # create new record
                cursor.execute("""
                    INSERT INTO `records` (UserName, DateOfBirth)
                    VALUES ('{0}', '{1}')
                """.format(username, dateofbirth))
                connection.commit()
                logger.info('## New record created in DB.')
            else:
                logger.info('## Update old record in DB.')
                # update old record
                cursor.execute("""
                    UPDATE `records`
                    SET DateOfBirth = '{0}' WHERE UserName = '{1}'
                """.format(dateofbirth, username))
                connection.commit()
                logger.info('## Old record updated in DB.')
    except pymysql.MySQLError as e:
        logger.error("** Failed update record in DB.")
        logger.error(e)
        return False
    # mark update complete
    return True

# get data for GET request
def get_record(username):
    global connection
    global cursor
    global get_request_response_message
    global get_request_response_code
    try:
        with connection.cursor() as cursor:
            # check for record
            cursor.execute("""
                SELECT dateofbirth
                FROM `records`
                WHERE UserName = '{0}'
            """.format(username))
            # failsafe handle for no record found.
            if cursor.rowcount < 1:
                logger.info('## No record found in DB.')
                get_request_response_code = 404
                get_request_response_message = "Sorry, username {0} is not found.".format(username)
            else:
                logger.info('## Record found in DB.')
                get_request_response_code = 200
                # get data from db, and translate datetime string to datetime obj for calculation
                cursor_result = cursor.fetchone()
                retrieved_dateofbirth = cursor_result[0]
                date_of_birth_obj = datetime.datetime.strptime(retrieved_dateofbirth, '%Y-%m-%d')
                current_date_obj = datetime.datetime.now()
                if date_of_birth_obj.day == current_date_obj.day and date_of_birth_obj.month == current_date_obj.month:
                    get_request_response_message = "Hello, {0}! Happy Birthday!".format(username)
                elif date_of_birth_obj.date() < current_date_obj.date():
                    # construct upcoming birthday date
                    coming_birthday_date_obj = datetime.datetime(current_date_obj.year, date_of_birth_obj.month, date_of_birth_obj.day)
                    # needed if the month and day of birhtday alrdy passed this year
                    if coming_birthday_date_obj.date() < current_date_obj.date():
                        coming_birthday_date_obj = datetime.datetime(current_date_obj.year+1, date_of_birth_obj.month, date_of_birth_obj.day)
                    difference = coming_birthday_date_obj - current_date_obj
                    get_request_response_message = "Hello, {0}! Your birthday is in {1} day(s)!".format(username, difference.days)
                else:
                    # failsafe handle for bad birth date found
                    get_request_response_code = 404
                    get_request_response_message = "Hello, {0}! Your birth date is far in future. You should not exist.".format(username)
    except pymysql.MySQLError as e:
        logger.error("** Failed finding record in DB.")
        logger.error(e)
        return False
    # mark get complete
    return True

# actual lambda function entry point
def lambda_handler(event, context):
    # 'event' default to dict, but can be list, str, int, float, or NoneType type
    # 'context' is runtime information for handler

    global connection
    global cursor
    global get_request_response_message
    global get_request_response_code

    # inspect incoming event
    logger.info('## Received EVENT data:')
    logger.info(event)

    # validate incoming event
    if not validate_http_request(event):
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "Bad Request."
            }),
        }

    # list of important data
    http_method = event["httpMethod"].upper()
    user_name = event["path"].replace(api_context_path, '', 1)
    user_birth_date = None

    # make sure can connect to DB
    if not check_database_connection():
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Internal Server Error."
            }),
        }

    # make sure DB is ready to use
    if not prep_database():
        connection.close()
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Internal Server Error."
            }),
        }

    # handle PUT request
    if http_method == 'PUT':
        json_http_body = json.loads(event["body"])
        date_of_birth_str = json_http_body["dateOfBirth"]
        if update_record(user_name, date_of_birth_str):
            connection.close()
            # Exit after processed PUT request successfully
            return {
                "statusCode": 204,
                "body": json.dumps({
                    "message": "No Content."
                }),
            }
        else:
            connection.close()
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "message": "Internal Server Error."
                }),
            }

    # handle GET request
    # get user_birth_date in date time obj
    if http_method == 'GET':
        get_record(user_name)
        connection.close()
        # taking response code and response message from global after set by get_record
        return {
            "statusCode": get_request_response_code,
            "body": json.dumps({
                "message": get_request_response_message
            }),
        }

    # close database connection
    connection.close()

    # default return bad request message
    return {
        "statusCode": 400,
        "body": json.dumps({
            "message": "Bad Request."
        }),
    }
