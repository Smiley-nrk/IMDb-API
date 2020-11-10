from scraper import scrap_movie_details, scrap_movie_list
import flask
import logging

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger()


app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route('/scrapDetails', methods=['GET'])
def scrap_details():
    LOGGER.info(" [x] new request to scrap details")
    try:
        scrap_movie_details()
        LOGGER.info(" [x] Sending response")
        return "Success"
    except Exception as ex:
        if hasattr(ex, 'message'):
            LOGGER.error(" [!] Error in scrap_details: " + ex.message)
        else:
            LOGGER.error(" [!] Error in scrap_details: " + ex.__str__())
        return "Error"


@app.route('/fetchList', methods=['GET'])
def fetch_list():
    LOGGER.info(" [x] new request to fetch movie list")
    try:
        movies = scrap_movie_list()
        LOGGER.info(" [x] Sending response")
        return dict((i, movie.__dict__) for i, movie in enumerate(movies))
    except Exception as ex:
        if hasattr(ex, 'message'):
            LOGGER.error(" [!] Error in fetch_list: " + ex.message)
        else:
            LOGGER.error(" [!] Error in fetch_list: " + ex.__str__())
        return "Error while fetching list"


app.run(port=8001)