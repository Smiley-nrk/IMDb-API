import json
from threading import Thread

import flask
import pymongo
from flask import request, abort
import requests
import logging
from werkzeug.exceptions import Unauthorized

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger()

app = flask.Flask(__name__)
app.config["DEBUG"] = True

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["IMDb"]
mycol = mydb["movies"]
SCRAPPER_URL = "http://localhost:8001"
UNDER_UPDATE_STR = "<h1>We are updating our data. Please try again after some time</h1>"
SORT_LOOKUP = {"name": "title", "rating": "rating", "releaseDate": "release_date_sortable",
               "duration": "duration_sortable"}


def set_valid_data_flag(value):
    global VALID_DATA
    VALID_DATA = value


VALID_DATA = True


def get_valid_data_flag():
    return VALID_DATA


@app.route('/addUser', methods=['GET'])
def add_new_user():
    LOGGER.info(" [+] New request to add new user")
    user_col = mydb["users"]
    try:
        if 'userName' in request.args:
            user_name = request.args['userName']
            user_col.insert_one({"_id": hash(user_name), "user": user_name})
            LOGGER.info(" [+] New user added with name:"+user_name+" and token:"+hash(user_name).__str__())
        else:
            raise Exception("userName argument is required!")

        return {"Token": hash(user_name)}
    except Exception as ex:
        if hasattr(ex, 'message'):
            LOGGER.error(" [!] Error while adding new user: " + ex.message)
        else:
            LOGGER.error(" [!] Error while adding new user: " + ex.__str__())
        return "<h1>Error while adding new user</h1>"


def authenticate(request):
    if 'bearerToken' not in request.headers:
        LOGGER.error(" [!] bearerToken not found in request headers")
        abort(401)
    token = request.headers['bearerToken']
    LOGGER.info(" [x] Authenticating for " + token)
    user_col = mydb["users"]
    x = user_col.find_one({"_id": int(token)})
    if x is None:
        LOGGER.error("Token " + token + " is not valid")
        abort(401)
    return True


def fetch_details():
    LOGGER.info(" [x] Sending fetch details request")
    r = requests.get(SCRAPPER_URL + "/scrapDetails")
    LOGGER.info(" [x] Received response for fetching detail request: " + r.text)
    if r.text == 'Success':
        set_valid_data_flag(True)
    else:
        LOGGER.error(" [!] Error while updating data!")
        # put some logic to send mail


def validate_db_data():
    LOGGER.info(" [x] Validating data in db with data fetched from internet")
    try:
        LOGGER.info(" [x] Fetching data from DB")
        movies_from_db = mycol.find({}, {"_id": 0, "link": 1, "title": 1, "rank": 1}).sort("rank")
        y = [y for y in movies_from_db]

        LOGGER.info(" [x] Fetched data from DB. Now fetching from internet")
        r = requests.get(SCRAPPER_URL + "/fetchList")
        x = [x for x in json.loads(r.text).values()]

        LOGGER.info(" [x] Fetched data from from internet")
        if x != y:
            set_valid_data_flag(False)
            LOGGER.info(" [x] INVALID DATA IN DB")
            t = Thread(target=fetch_details)
            t.start()
            return False
        else:
            LOGGER.info(" [x] VALID DATA IN DB")
            return True
    except Exception as ex:
        if hasattr(ex, 'message'):
            LOGGER.error(" [!] Error while validating DB data: " + ex.message)
        else:
            LOGGER.error(" [!] Error while validating DB data: " + ex.__str__())
        raise


@app.route('/movies/all', methods=['GET'])
def get_all_movies():
    LOGGER.info(" [x] New request to get all movies")
    try:
        authenticate(request)
        LOGGER.info(" [x] Request authenticated")
        if not get_valid_data_flag():
            return UNDER_UPDATE_STR
        if not validate_db_data():
            return UNDER_UPDATE_STR

        LOGGER.info(" [x] DB data valid. Now preparing response")
        movies = mycol.find({}, {"_id": 0, "link": 0})
        if 'sortBy' in request.args:
            sort_by = request.args['sortBy']
            if 'desc' in request.args and request.args['desc']:
                movies = movies.sort(SORT_LOOKUP[sort_by], -1)
            else:
                movies = movies.sort(SORT_LOOKUP[sort_by])

        return dict((i, movie) for i, movie in enumerate(movies))
    except Unauthorized as ex:
        LOGGER.error(" [!] Unauthorized request")
        raise
    except Exception as ex:
        if hasattr(ex, 'message'):
            LOGGER.error(" [!] Error while getting all movies: " + ex.message)
        else:
            LOGGER.error(" [!] Error while getting all movies: " + ex.__str__())
        return "<h1>Error while fetching info</h1>"


@app.route('/movie', methods=['GET'])
def get_movie():
    LOGGER.info(" [x] New request to get specific movie")
    try:
        authenticate(request)
        LOGGER.info(" [x] Request authenticated")

        if not get_valid_data_flag():
            return UNDER_UPDATE_STR
        if not validate_db_data():
            return UNDER_UPDATE_STR

        LOGGER.info(" [x] DB data valid. Now preparing response")
        if 'name' in request.args:
            name = request.args['name']
            LOGGER.info(" [x] searching for title: " + name)
            movies = mycol.find({"title": {"$regex": name, "$options": "i"}}, {"_id": 0, "link": 0})
        elif 'desc' in request.args:
            desc = request.args['desc']
            LOGGER.info(" [x searching for desc having: " + desc)
            movies = mycol.find({"summary": {"$regex": ".*" + desc + ".*", "$options": "i"}}, {"_id": 0, "link": 0})
        else:
            raise Exception("Either of name or desc parameter required for this API")

        return dict((i, movie) for i, movie in enumerate(movies))
    except Unauthorized as ex:
        LOGGER.error(" [!] Unauthorized request")
        raise
    except Exception as ex:
        if hasattr(ex, 'message'):
            LOGGER.error(" [!] Error while getting all movies: " + ex.message)
        else:
            LOGGER.error(" [!] Error while getting all movies: " + ex.__str__())
        return "<h1>Error while fetching info: "+ex.args[0]+"</h1>"


app.run()
