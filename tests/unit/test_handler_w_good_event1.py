import os
import json
import pytest
import pymysql
import cryptography
import datetime

from hello_world import app

# for checking database can connect
def db_connected():
    db_server_host = '127.0.0.1'
    db_port = 3306
    db_name = 'sam'
    db_user_name = 'sam'
    db_user_password = 'sam'
    try:
        connection = pymysql.connect(host=db_server_host, user=db_user_name, passwd=db_user_password, db=db_name, port=db_port, connect_timeout=5)
        cursor = connection.cursor()
        print('## Connected to DB.')
    except pymysql.MySQLError as e:
        print("** Failed connection to DB.")
        print(e)
        return False
    # mark database connection good
    return True

@pytest.fixture(scope="session")

# use docker to spawn test db
def docker_compose_file(pytestconfig):
    return os.path.join(str(pytestconfig.rootdir), "./", "docker-compose.yml")

# actual test
def test_lambda_handler(docker_services):
    # force wait for db service to be ready before proceed test
    docker_services.wait_until_responsive(
        timeout=60.0, pause=5, check=lambda: db_connected()
    )

    # prep list of good events
    with open('events/api_good_event1.json') as f:
        good_event_1 = json.load(f)

    with open('events/api_good_event2.json') as f:
        good_event_2 = json.load(f)

    with open('events/api_good_event3.json') as f:
        good_event_3 = json.load(f)

    with open('events/api_good_event4.json') as f:
        good_event_4 = json.load(f)

    # test GET request on username
    # expect no data for username because no data inserted yet
    ret = app.lambda_handler(good_event_2, "")
    data = json.loads(ret["body"])

    assert ret["statusCode"] == 404
    assert "message" in ret["body"]
    assert data["message"] == "Sorry, username username is not found."

    # test PUT request to insert first good data
    # date is end of the year
    ret2 = app.lambda_handler(good_event_1, "")
    data2 = json.loads(ret2["body"])

    # calculate exact days till birthday
    body_msg_good_event_1 = json.loads(good_event_1["body"])
    date_of_birth_str_event_1 = body_msg_good_event_1["dateOfBirth"]
    date_of_birth_str_event_1_obj = datetime.datetime.strptime(date_of_birth_str_event_1, '%Y-%m-%d')
    current_date_obj = datetime.datetime.now()
    if date_of_birth_str_event_1_obj.date() < current_date_obj.date():
        coming_birthday_date_obj = datetime.datetime(current_date_obj.year, date_of_birth_str_event_1_obj.month, date_of_birth_str_event_1_obj.day)
        if coming_birthday_date_obj.date() < current_date_obj.date():
            coming_birthday_date_obj = datetime.datetime(current_date_obj.year+1, date_of_birth_str_event_1_obj.month, date_of_birth_str_event_1_obj.day)
        difference = coming_birthday_date_obj - current_date_obj

    assert ret2["statusCode"] == 204
    assert "message" in ret2["body"]
    assert data2["message"] == "No Content."

    # test GET request on username again after inserted data
    # this is checking days to last day of the year
    ret3 = app.lambda_handler(good_event_2, "")
    data3 = json.loads(ret3["body"])

    assert ret3["statusCode"] == 200
    assert "message" in ret3["body"]
    assert data3["message"] == "Hello, username! Your birthday is in {0} day(s)!".format(difference.days)

    # test PUT request to insert second good data
    # date is start of the year
    ret4 = app.lambda_handler(good_event_3, "")
    data4 = json.loads(ret4["body"])

    # calculate exact days till birthday
    body_msg_good_event_3 = json.loads(good_event_3["body"])
    date_of_birth_str_event_3 = body_msg_good_event_3["dateOfBirth"]
    date_of_birth_str_event_3_obj = datetime.datetime.strptime(date_of_birth_str_event_3, '%Y-%m-%d')
    if date_of_birth_str_event_3_obj.date() < current_date_obj.date():
        coming_birthday_date_obj = datetime.datetime(current_date_obj.year, date_of_birth_str_event_3_obj.month, date_of_birth_str_event_3_obj.day)
        if coming_birthday_date_obj.date() < current_date_obj.date():
            coming_birthday_date_obj = datetime.datetime(current_date_obj.year+1, date_of_birth_str_event_3_obj.month, date_of_birth_str_event_3_obj.day)
        difference = coming_birthday_date_obj - current_date_obj

    assert ret4["statusCode"] == 204
    assert "message" in ret4["body"]
    assert data4["message"] == "No Content."

    # test GET request on username again after inserted data
    # this is checking days to first day of the year
    ret3 = app.lambda_handler(good_event_2, "")
    data3 = json.loads(ret3["body"])

    assert ret3["statusCode"] == 200
    assert "message" in ret3["body"]
    assert data3["message"] == "Hello, username! Your birthday is in {0} day(s)!".format(difference.days)

    # test PUT request to insert third good data
    # create a date which is exactly 10 years ago from today
    date_obj_10_years_ago = datetime.datetime(current_date_obj.year-10, current_date_obj.month, current_date_obj.day)
    tmp_new_date = {'dateOfBirth': date_obj_10_years_ago.strftime('%Y-%m-%d')}
    good_event_4["body"] = json.dumps(tmp_new_date)
    ret5 = app.lambda_handler(good_event_4, "")
    data5 = json.loads(ret5["body"])

    assert ret5["statusCode"] == 204
    assert "message" in ret5["body"]
    assert data5["message"] == "No Content."

    # test GET request on username again after insert data
    # this is checking output based on date with exact 10 years ago
    ret6 = app.lambda_handler(good_event_2, "")
    data7 = json.loads(ret6["body"])

    assert ret6["statusCode"] == 200
    assert "message" in ret6["body"]
    assert data7["message"] == "Hello, username! Happy Birthday!"
