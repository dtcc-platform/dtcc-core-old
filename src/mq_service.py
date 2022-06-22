#!/usr/bin/env python
import pika, logging
# todo, add logging function
logger = logging.getLogger(__name__)
## example of usage of sender
###
###    service = MQService('rabbitmq', "user_management")
###	   service.publish_and_close_connection("msg")
###
class RabbitPub:
    def __init__(self, host:str,channel:str, port=5672):
        self.host = host
        self.port = port
        self.channel = channel
        self.connection = None
        self.channel = None

    def create_connection(self):
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host,port=self.port))
            self.channel = self.connection.channel()
            # durable to make queue persistent, survive mq server restart
            # todo, no need to declare queue every time? waste of resource
            self.channel.queue_declare(queue=self.channel,durable=True)
        except BaseException as e:
            logger.exception(str(e))

    def publish(self, msg):
        try:
            self.create_connection()
            self.channel.basic_publish(
                routing_key=self.queue_name,
                exchange = '',
                body=msg,
                properties=pika.BasicProperties(
                    delivery_mode = 2, # make message persistent
                )
            )
        except Exception as e:
            print(str(e))
        finally:
            if (self.connection is not None):
                self.connection.close()

    def callback(self,ch, method, properties, body, message_consumer):
        try:
            message_consumer(body)
            ch.basic_ack(delivery_tag = method.delivery_tag)
        except BaseException as e:
            logger.exception(str(e))

    def consume(self,message_consumer):
        self.create_connection()
        self.channel.basic_consume(queue=self.channel, on_message_callback=self.callback)
        self.channel.start_consuming()