import requests
from bs4 import BeautifulSoup
import time
from threading import Thread
from queue import Queue
import pika
import json
import logging
from datetime import datetime
from bson import json_util

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger()


class Movie:
    def __init__(self, title, duration, duration_sortable, release_date, release_date_sortable, rating, summary, link, rank):
        self.title = title
        self.duration = duration
        self.release_date = release_date
        self.rating = rating
        self.summary = summary
        self.link = link
        self.rank = rank
        self.release_date_sortable = release_date_sortable
        self.duration_sortable = duration_sortable

    def __init__(self, link, rank, title):
        self.link = link
        self.rank = rank
        self.title = title


def scrap_movie_list():
    LOGGER.info(" [x] Scrapping movie list")
    try:
        r = requests.get("https://www.imdb.com/chart/top?ref_=nv_mv_250")
        soup = BeautifulSoup(r.text, "html.parser")
        movie_list = soup.find_all("td", class_="titleColumn")

        movies = []
        for i, movie in enumerate(movie_list):
            movies.append(Movie(link=movie.a.get("href"), rank=i+1, title=movie.a.text))

        LOGGER.info(" [x] Found " + len(movies).__str__() + " movies from link")
        return movies
    except Exception as ex:
        if hasattr(ex, 'message'):
            LOGGER.error(" [!] Error in scrap_movie_list: " + ex.message)
        else:
            LOGGER.error(" [!] Error in scrap_movie_list: " + ex.__str__())
        raise


def scrap_movie_details():
    LOGGER.info(" [x] Scrapping movie details")
    try:
        movies = scrap_movie_list()
        fetch_detail_for_each_movie(movies)
    except Exception as ex:
        if hasattr(ex, 'message'):
            LOGGER.error(" [!] Error in scrap_movie_details: " + ex.message)
        else:
            LOGGER.error(" [!] Error in scrap_movie_details: " + ex.__str__())
        raise


def fetch_detail_for_each_movie(movies):
    LOGGER.info(" [x] Fetching details for " + len(movies).__str__() + " movies")
    LOGGER.info(" [x] Connecting to detailedListQueue to send 'START' msg.")
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='detailedListQueue')
        LOGGER.info(" [x] Connection to detailedListQueue SUCCESSFUL")

        channel.basic_publish(exchange='', routing_key='detailedListQueue', body="START")
        q = Queue()
        for movie in movies:
            q.put(movie)

        start = time.time()
        for i in range(25):
            t = Thread(target=fetch_details, args=(q, ))
            t.start()
        q.join()
        LOGGER.info(" [x] Scrapping Complete")
    except Exception as ex:
        if hasattr(ex, 'message'):
            LOGGER.error(" [!] Error in fetch_detail_for_each_movie: " + ex.message)
        else:
            LOGGER.error(" [!] Error in fetch_detail_for_each_movie: " + ex.__str__())
        raise
    finally:
        connection.close()
        LOGGER.info(" [x] Time Taken="+((time.time() - start)/60).__str__()+" Min")


def try_parsing_date(text):
    for fmt in ('%d %B %Y', '%B %Y', '%Y'):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError('no valid date format found')


def fetch_details(q):
    LOGGER.info(" [x] fetching details")
    LOGGER.info(" [x] Connecting to detailedListQueue to send details")
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='detailedListQueue')
        LOGGER.info(" [x] Connection to detailedListQueue SUCCESSFUL")

        while not q.empty():
            movie = q.get()
            r = requests.get("https://www.imdb.com/"+movie.link)
            soup = BeautifulSoup(r.text, "html.parser")
            movie.title = soup.find("h1").contents[0].strip()
            movie.duration = soup.find_all("time").pop().text.strip()
            movie.duration_sortable = int(movie.duration[:-4])
            movie.release_date = soup.find(title="See more release dates").text.strip()
            x = movie.release_date
            movie.release_date_sortable = try_parsing_date(x[:x.find("(") - 1])
            movie.rating = float(soup.find(itemprop="ratingValue").text.strip())
            movie.summary = soup.find(class_="summary_text").text.strip()
            channel.basic_publish(exchange='', routing_key='detailedListQueue', body=json.dumps(movie.__dict__, default=json_util.default))
            LOGGER.info(" ["+movie.rank.__str__()+"] Sent " + json.dumps(movie.__dict__, default=json_util.default))
            q.task_done()
    except Exception as ex:
        if hasattr(ex, 'message'):
            LOGGER.error(" [!] Error in fetch_detail: " + ex.message)
        else:
            LOGGER.error(" [!] Error in fetch_detail: " + ex.__str__())
        raise
    finally:
        connection.close()