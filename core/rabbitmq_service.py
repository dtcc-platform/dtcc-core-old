import os, pathlib, sys, json, uuid, time, asyncio, logging, datetime
import multiprocessing, threading, functools
import pika
import aio_pika

logging.getLogger("pika").setLevel(logging.WARNING)

project_dir = str(pathlib.Path(__file__).resolve().parents[0])
sys.path.append(project_dir)

from utils import try_except
from logger import getLogger
from minio_progress import BaseProgress, format_string, _REFRESH_CHAR

logger = getLogger(__file__)

from base64 import b64encode, b64decode

rabbitmq_host =   os.environ.get("RABBITMQ_HOST", "localhost")
rabbitmq_user = os.environ.get("RABBITMQ_USER", "dtcc_rmq" )
rabbitmq_password = os.environ.get("RABBITMQ_PASSWORD", "dtcc_rmq")
rabbitmq_port = 5672

amq_url = f"amqp://{rabbitmq_user}:{rabbitmq_password}@{rabbitmq_host}:5672/"

async def log_consumer(request, queue_name = "test_queue") -> None:
    connection = await aio_pika.connect_robust(
        amq_url,
    )

    async with connection:
        # Creating channel
        channel = await connection.channel()

        # Will take no more than 10 messages in advance
        # await channel.set_qos(prefetch_count=10)

        # Declaring queue
        queue = await channel.declare_queue(queue_name, auto_delete=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                if await request.is_disconnected():
                    print("client disconnected!!!")
                    break
                async with message.process():
                    yield message.body.decode()

                    if queue.name in message.body.decode():
                        break
                time.sleep(0.01)
            

async def test_log_consumer(queue_name = "test_queue") -> None:
    connection = await aio_pika.connect_robust(
        amq_url,
    )

    async with connection:
        # Creating channel
        channel = await connection.channel()

        # Will take no more than 10 messages in advance
        # await channel.set_qos(prefetch_count=10)

        # Declaring queue
        queue = await channel.declare_queue(queue_name, auto_delete=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:

                async with message.process():
                    print(json.loads(message.body.decode()))
                    # yield json.loads(message.body.decode())
                    if queue.name in message.body.decode():
                        break
                # time.sleep(0.5)


async def get_publish_channel():
    connection = await aio_pika.connect(amq_url)
    channel = await connection.channel()
    return channel

async def publish_async(queue_name:str, message:dict):
    message['timestamp'] = datetime.datetime.now().isoformat()
    channel = await get_publish_channel()
    await channel.default_exchange.publish(
        aio_pika.Message(body=json.dumps(message).encode()),
        routing_key=queue_name,
    )

## TODO Make new pubsub asynchronous class
class PikaPubSub:

    def __init__(self, queue_name):
        self.queue_name = queue_name
        self.creds = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
        self.create_connection()
        
    @try_except(logger=logger)
    def create_connection(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=rabbitmq_host,port=rabbitmq_port, credentials=self.creds )
        )
        self.channel = self.connection.channel()
        logger.info('Pika connection established')
        return self.connection, self.channel
        
    def publish(self,message: dict):
        try:
            connection, channel = self.create_connection()
            pub = threading.Thread(target=self.callback_publish, args=(channel,message))
            pub.start()
            
            # cb = functools.partial(self.callback_publish, channel, message)
            # connection.add_callback_threadsafe(cb)

            return True
        except:
            logger.exception(f"from publish {message.__str__()}")
            return False

    def callback_publish(self, channel, message: dict):
        """Method to publish message to RabbitMQ"""
        message['timestamp'] = datetime.datetime.now().isoformat()
        try:
           channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=json.dumps(message).encode()
            )
        except:
            logger.exception(str(message))

    def subscribe(self, on_mesage_callback):
        connection, channel = self.create_connection()

        try:
            # channel.exchange_declare(exchange="dtcc", exchange_type="direct", passive=False, durable=True, auto_delete=False)
            channel.queue_declare(queue=self.queue_name)
            # self.channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=self.queue_name, on_message_callback=on_mesage_callback)

            channel.start_consuming()
        except KeyboardInterrupt:
            channel.close()
            connection.close()
        except pika.exceptions.ConnectionWrongStateError:
            self.subscribe(on_mesage_callback)
        except:
            logger.exception("from pubsub subscribe!!!!!!")

    ## TODO subscribe one using consume, cancel consume method

    
    @try_except(logger=logger)
    def close_connection(self):
        try:
            if (self.connection is not None):
                if self.channel.is_open:
                    self.channel.close()
                if self.connection.is_open:
                    self.connection.close()
        except pika.exceptions.StreamLostError:
            logger.info("pika error")
        except:
            logger.info("pika error")


    def __example_callback(self, ch, method, properties, body):
        print(" [x] Received %r" % body)
        time.sleep(body.count(b'.'))
        print(" [x] Done")
        ch.basic_ack(delivery_tag=method.delivery_tag)



class PikaProgress(BaseProgress):
    def __init__(self, module, tool, task_id, channel, interval=1, stdout=sys.stdout):
        super().__init__(interval, stdout)
        self.module = module
        self.tool = tool
        self.task_id = task_id
        self.client = PikaPubSub(queue_name=channel)

    def emit_status(self, current_size, total_length, displayed_time, prefix):

        formatted_str = prefix + format_string(
            current_size, total_length, displayed_time)
        self.stdout.write(_REFRESH_CHAR + formatted_str + ' ' *
                          max(self.last_printed_len - len(formatted_str), 0))
        message = {"module": self.module, "tool": self.tool, "task_id":self.task_id, "current_size":current_size, "total_length":total_length, "prefix":prefix }
        self.client.publish(message=message)

        self.stdout.flush()
        self.last_printed_len = len(formatted_str)

if __name__=='__main__':
    asyncio.run(test_log_consumer(queue_name='/task/dtcc/generate-citymodel/logs'))
    