import time, logging
import redis
from typing import Union

logger = logging.getLogger(__name__)

class RedisPubSub():
    def __init__(self,host:str, port:int) -> None:
        self.client = redis.Redis(host=host, port=port, password="dtcc_redis", decode_responses=True)
        
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
                time.sleep(0.1)
            except Exception as e:
                logger.exception("from redis publish: "+str(e))
            
            if retries>=retry_limit:
                logger.error(f"Failed to send {message} to {channel} no receivers")
                break
            else:
                time.sleep(0.1)
            retries += 1
        return published       

    def subscribe(self,channel:str,retry_limit=5) -> Union[str, None]:
        self.pubsub = self.client.pubsub(ignore_subscribe_messages=True)
        self.pubsub.subscribe(channel)
        message = None
        # retries = 0 
        while True:
            try:
                message = self.pubsub.get_message()
                if message and (not message['data'] == 1):
                    message = message['data']
                    break
            except redis.ConnectionError as e:
                logger.error(e)
                logger.error("Will attempt to retry")
                
            except Exception as e:
                logger.exception("from redis subscribe: "+str(e))
            
            # if False: #retries>=retry_limit:
            #     logger.error(f"Failed to receive message from {channel}")
            #     break
            # else:
            time.sleep(0.1)
            # retries += 1
        return message



    



def test_pubsub():
    rps = RedisPubSub(host='localhost',port=6879)
    channel = "test"
    msg = 'It is working!'
    published = rps.publish(channel=channel,message=msg)

    if published:
        incoming_msg = rps.subscribe(channel=channel)
        print(incoming_msg)
        assert msg == incoming_msg


    
test_pubsub()