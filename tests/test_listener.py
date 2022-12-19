import time, pathlib, sys, datetime


project_dir = str(pathlib.Path(__file__).resolve().parents[1])
sys.path.append(project_dir)

from data_models import ModuleStatus
from rabbitmq_service import PikaPubSub
from registry_manager import RegistryManager

def get_time_diff_in_minutes(iso_timestamp:str):
    diff = datetime.datetime.now() - datetime.datetime.fromisoformat(iso_timestamp)
    minutes, seconds = divmod(diff.total_seconds(), 60) 
    return int(minutes)

def test():
    registry_manager = RegistryManager()
    registry_manager.listen_for_modules()

    for i in range(3):
        print(f"Running test number: {i}")

        valid = False
        while True:
            registered_modules = list(registry_manager.get_available_modules().values())
            for registered_module in registered_modules:
                if get_time_diff_in_minutes(registered_module.last_seen) < 2 and registered_module.status == ModuleStatus.waiting.value:
                    print("modules registred!")
                    valid = True
            if valid:
                break
            
            else:
                print("....")
            time.sleep(1)
            
        print("....#######")
        check_count = 0
        for registered_module in registered_modules:
            
            if get_time_diff_in_minutes(registered_module.last_seen) < 2 and registered_module.status == ModuleStatus.waiting.value :

                channel = f"/task/{registered_module.token}"

                pub_sub = PikaPubSub(queue_name=channel)

                
                pub_sub.publish(message={"cmd":"start"})

                time.sleep(5)

                module_registry_data = registry_manager.get_module_data(registered_module.task_id)
                print(module_registry_data)

                if module_registry_data.status == ModuleStatus.success.value:
                    print(f"{i}: success!!!!!!!")
                    break

                pub_sub.publish(message={"cmd":"pause"})
                for i in range(3):
                    print(i)
                    time.sleep(1)

                pub_sub.publish(message={"cmd":"resume"})
                for i in range(2):
                    print(i)
                    time.sleep(1)

                pub_sub.publish(message={"cmd":"stop"})
                

        
                time.sleep(5)

                module_registry_data = registry_manager.get_module_data(registered_module.task_id)
                print(module_registry_data)

                if module_registry_data.status == ModuleStatus.terminated.value:
                    print(f"{i}: success!!!!!!!")
                else:
                    print("################--------->", module_registry_data.status)

                break
            else:
                check_count += 1

        if check_count==len(registered_modules):
            if len(registered_modules)>0:
                print("no lastest modules found")
            else:
                print("no modules found")


            
    registry_manager.close()


if __name__=='__main__':
    test()