import os
import json

import pytest

from hello_world import app

@pytest.fixture()

# bad event 6 : PUT request with invalid json format body data
def test_event():
    with open('events/api_bad_event6.json') as f:
        bad_event = json.load(f)

    return bad_event

def test_lambda_handler(test_event, mocker):

    ret = app.lambda_handler(test_event, "")
    data = json.loads(ret["body"])

    assert ret["statusCode"] == 400
    assert "message" in ret["body"]
    assert data["message"] == "Bad Request."
