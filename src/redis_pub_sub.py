import time, logging
import redis

logger = logging.getLogger(__name__)

class RedisPublisher():
    def __init__(self,host:str, port:int) -> None:
        self.client = redis.Redis(host=host, port=port, decode_responses=True)
        
    def test_redis(self) -> None:
        test_key = 'test'
        test_msg = 'It is working!'
        self.client.set(test_key, test_msg )
        
        assert test_msg == self.client.get(test_key)

    def publish(self, channel:str, message:str,retry_limit=5) -> bool:
        retries = 0
        published = False
        while True:
            try:
                rcvd = self.client.publish(channel, message)
                if rcvd >0:
                    logger.info("Success!")
                    published = True
                    break
            except redis.ConnectionError as e:
                logger.error(e)
                logger.error("Will attempt to retry")
            except Exception as e:
                logger.exception("from publish: "+str(e))
            
            if retries>=retry_limit:
                logger.error(f"Failed to send {message} to {channel}")
                break
        return published       


class RedisSubscriber():
    def __init__(self,host:str, port:int, channel:str, callback=None) -> None:
        self.client = redis.Redis(host=host, port=port, decode_responses=False)
        self.pubsub = self.client.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(channel)
        self.callback = callback

    def test_redis(self):
        test_key = 'test'
        test_msg = 'It is working!'
        self.client.set(test_key, test_msg )
        
        assert test_msg == self.client.get(test_key)

    def subscribe(self):
        message = None
        count = 0
        while True:
            message = self.pubsub.get_message()

            if message and (not message['data'] == 1):
                message = message['data'].decode('utf-8')
                break

            count += 1
            if (count % 10) == 0:
                if (callable(self.callback)):
                    try:
                        self.callback(self, count)
                    except:
                        pass
                time.sleep(0.1)
        return message



def test_pubsub():
    pass
    
    