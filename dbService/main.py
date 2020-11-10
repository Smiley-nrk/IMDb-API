import json
import pika
import pymongo
import logging
from bson import json_util

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger()


def callback(ch, method, properties, body):
    try:
        body = body.decode()
        myclient = pymongo.MongoClient("mongodb://localhost:27017/")
        mydb = myclient["IMDb"]
        mycol = mydb["movies"]
        if body == "START":
            LOGGER.info(" [!] new stream starting")
            x = mycol.delete_many({})
            LOGGER.info(x.deleted_count.__str__() + " documents deleted.")
        else:
            LOGGER.info(" [x] Received " + body)
            movie = json.loads(body, object_hook=json_util.object_hook)
            movie['_id'] = movie['rank']
            x = mycol.insert_one(movie)
    except Exception as ex:
        if hasattr(ex, 'message'):
            LOGGER.error("Error while consuming RabbitMQ - detailedListQueue: " + ex.message)
        else:
            LOGGER.error("Error while consuming RabbitMQ - detailedListQueue: " + ex.__str__())
        raise


try:
    LOGGER.info(" [+] Connecting to RabbitMQ")
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='detailedListQueue')
    channel.basic_consume(queue='detailedListQueue', on_message_callback=callback, auto_ack=True)

    LOGGER.info(' [*] Waiting for messages.')
    channel.start_consuming()
except Exception as ex:
    if hasattr(ex, 'message'):
        LOGGER.error("Error while connecting to RabbitMQ - detailedListQueue: " + ex.message)
    else:
        LOGGER.error("Error while connecting to RabbitMQ - detailedListQueue: " + ex.__str__())
finally:
    connection.close()
