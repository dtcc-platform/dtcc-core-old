import time, pathlib, sys, datetime, multiprocessing, json, threading

from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional
from enum import Enum, IntEnum

project_dir = str(pathlib.Path(__file__).resolve().parents[0])
sys.path.append(project_dir)

from logger import getLogger
from utils import try_except, DictStorage
from rabbitmq_service import PikaPubSub
from data_models import ModuleRegistry, ModuleStatus

logger = getLogger(__file__)


class RegistryManager():
    def __init__(self) -> None:
        self.channel = "/tasks/registry"
        self.module_registry = DictStorage(file_name="pubsub_module_registry")
        self.isListening = False
        self.listening_event = threading.Event()
    
    def register_module(self,module_registry_message:dict ):
        self.pika_pub_sub = PikaPubSub(queue_name=self.channel)
        self.pika_pub_sub.publish(message=module_registry_message)
    
    def get_available_modules(self):
        return self.module_registry.data

    def check_if_module_is_registered(self, task_id:str) -> bool:
        return self.module_registry.exists(task_id)

    def get_module_data(self, task_id:str) -> ModuleRegistry:
        return self.module_registry.retreive(task_id)
    
    def listen_for_modules(self):
        self.isListening = True
        self.listening_event.clear()
        listener = threading.Thread(target=self.__listen_handler, args=())
        listener.start()

    def __listen_handler(self):
        self.pika_pub_sub = PikaPubSub(queue_name=self.channel)
        try:
            while self.isListening:
                if self.listening_event.is_set():
                    break
                logger.info(f"Waiting for  {self.channel}")
                self.pika_pub_sub.subscribe(self.__update_module_registry)
                time.sleep(0.5)
        except BaseException:
            logger.exception("from Registry Manager")
            sys.exit(1)
    
    def __update_module_registry(self, ch, method, properties, body):
        print(" [x] Received %r" % body)
        
        ch.basic_ack(delivery_tag=method.delivery_tag)

        if body is not None: 
            message = json.loads(body)
            module_data = ModuleRegistry.parse_obj(message)
            self.module_registry.update(
                key=module_data.task_id,
                value=module_data
            )

    def save(self):
        self.module_registry.save()
    
    def load(self):
        self.module_registry.load()

    def close(self):
        self.isListening = False
        self.listening_event.set()
        


    