#!/usr/bin/env python3

import importlib, inspect
import multiprocessing, threading
from multiprocessing.pool import ThreadPool, Pool

def get_available_tools():
    tools = []
    for name, cls in inspect.getmembers(importlib.import_module("tools"), inspect.isclass):
        if cls.__module__ == "tools":
            tools.append((name,cls))
    return tools



def main():

    tools = get_available_tools()
    
    if len(tools)>0:
        
        # Spawn non blocking processes
        for name, cls in tools[:-1]:
            print(name)
            tool = threading.Thread(target=cls(publish=True).listen)
            tool.start()

        # Spawn one blocking process
        name, cls = tools[-1]
        print(name)
        cls(publish=True).listen()

    else:
        print("No tools available!")


if __name__=='__main__':
    main()