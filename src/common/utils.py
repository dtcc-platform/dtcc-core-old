import os, sys, pathlib, errno, time, functools, json, uuid, subprocess, shutil
import traceback
from urllib.request import urlretrieve
from types import ModuleType
from tqdm import tqdm

project_dir = pathlib.Path(__file__).resolve().parents[2]

class AttrDict(dict):
  __getattr__ = dict.__getitem__
  __setattr__ = dict.__setitem__

def mkdir_p(path, folder_name = None):
    if folder_name:
        abs_folder_path = os.path.join(path, folder_name)
    else:
        abs_folder_path = path
    try:
        os.makedirs(abs_folder_path)
        
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(abs_folder_path):
            pass
        else:
            raise
    return abs_folder_path   

def file_exists(path, min_size_mb=None):
    try:
        exists = os.path.exists(path)
        if exists:
            size = os.path.getsize(path)/1024*1024
            if size>0:
                if min_size_mb is not None: 
                    if size>=min_size_mb:
                        return True
                else:
                    return True
        
        return False
    except:
        return False


def get_size_mb(path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return int(total_size / (1024 * 1024))

def find_all_files_in_folder(folder, extension):
    if os.path.exists(folder):
        paths= []
        check_paths = []
        for path, subdirs, files in os.walk(folder):
            for file_path in files:
                if file_path.endswith(extension) and not file_path.startswith('.'):
                    if not any(file_path in s for s in check_paths):
                        paths.append(os.path.join(path , file_path))
                        check_paths.append(file_path)
        return paths
    else:
        raise Exception("path does not exist -> "+ folder)
        
def find_files_in_folder(folder, extension):
    if os.path.exists(folder):
        paths= []
        for file in os.listdir(folder):
            if file.endswith(extension):
                paths.append(os.path.join(folder , file))

        return paths
    else:
        raise Exception("path does not exist -> "+ folder)

def get_uuid(size=8):
    return str(uuid.uuid4())[:size]

def dict_from_module(module):
    context = {}
    for setting in dir(module):
        if not setting.startswith("_") and not setting.startswith("logger"):
            v = getattr(module, setting)
            if not isinstance(v, ModuleType):
                val = getattr(module, setting)
                if setting.endswith("dir") or "path" in setting:
                    val = val.replace(str(project_dir), '*')
                context[setting] = val
    return context



def dump_jsonl(data, output_path, append=False) -> None:
    """
    Write list of objects to a JSON lines file.
    """
    try:
        mode = 'a+' if append else 'w'
        with open(output_path, mode, encoding='utf-8') as f:
            for line in data:
                json_record = json.dumps(line, ensure_ascii=False)
                f.write(json_record + '\n')
        # print('Wrote {} records to {}'.format(len(data), output_path))
    except:
        raise Exception(f"Cannot save to {output_path}")
    

def load_jsonl(input_path:str) -> list:
    """
    Read list of objects from a JSON lines file.
    """
    try:
        data = []
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                data.append(json.loads(line.rstrip('\n|\r')))
        # print('Loaded {} records from {}'.format(len(data), input_path))
        return data
    except:
        raise Exception(f"Cannot load from {input_path}")

class TqdmUpTo(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)

def download_url(url, filepath):
    directory = os.path.dirname(os.path.abspath(filepath))
    os.makedirs(directory, exist_ok=True)
    if os.path.exists(filepath):
        print("Filepath already exists. Skipping download.")
        return

    with TqdmUpTo(unit="B", unit_scale=True, unit_divisor=1024, miniters=1, desc=os.path.basename(filepath)) as t:
        urlretrieve(url, filename=filepath, reporthook=t.update_to, data=None)
        t.total = t.n

def extract_archive(filepath):
    extract_dir = os.path.dirname(os.path.abspath(filepath))
    shutil.unpack_archive(filepath, extract_dir)


class Progress:
    def __init__(self,max_len, process_name):
        self.max_len = max_len
        self.process_name = process_name
        self.start_time = time.time()
        self.last_update_time = time.time()
        self.current_index = 0

    def update(self,n=1):
        self.current_index += n
        percent = int(self.current_index/self.max_len*100)
        current_time = time.time()
        iter_time = int(current_time - self.last_update_time)
        total_time = current_time - self.start_time
        self.last_update_time = current_time
        total_time_min = round(total_time/60, 2)
        eta = round(abs(round(((self.max_len * total_time)/self.current_index)/60,ndigits=2) - total_time_min),ndigits=2)
        print(f"{self.process_name} :: {self.current_index} out of {self.max_len} complete {percent}% iter {iter_time}s -- elapsed {total_time_min}min  --ETA {eta}min")


def launch_tensorboard(logdir, port=6006):
    if os.name == "posix":
        subprocess.Popen("sudo killall tensorboard", shell=True)
    command = "tensorboard --logdir="+ logdir + " --host 0.0.0.0 --port "+ str(port)
    subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    print("tensorboard launched at 0.0.0.0:"+ str(port))


def timer(func,logger=None):
    """Print the runtime of the decorated function"""
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        start_time = time.perf_counter()    # 1
        value = func(*args, **kwargs)
        end_time = time.perf_counter()      # 2
        run_time = round((end_time - start_time),4)    # 3
        msg = "Finished " + str(func.__name__) + " in "+ str(run_time) + " secs"
        if logger:
            logger.info(msg)
        else:
            print(msg)
        return value
    return wrapper_timer

def try_except(func, *args, **kwargs):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try: 
            return func(*args, **kwargs)
        except:
            msg = "from>>"+str(func.__name__)
            if kwargs.__contains__('logger'):
                kwargs['logger'].exception(msg)
            else:
                print(msg)
            return False
    return wrapper

class DictStorage():
    def __init__(self,file_name) -> None:
        self.file_name = file_name
        self.data = self.load()
        
    def update(self, key, value):
        self.data.update({key:value})

    def multiple_update(self,data_dict):
        self.data.update(data_dict)
    
    def retreive(self,key):
        return self.data[key]

    def load(self):
        data = {}
        if file_exists(self.file_name):
            data = json.load(open(self.file_name,'r'))  

        return data
    
    def save(self):
        saved = self.load()
        saved.update(self.data)
        json.dump(saved,open(self.file_name,'w'),indent=4)

from multiprocessing import Process, Manager, Pool


class MultiprocessManager():
    def __init__(self,max_jobs=12) -> None:
        self.max_jobs = max_jobs
        self.jobs = []

    def callback_wrapper(self,args):
        index = args[0]; row = args[1]; callback_function = args[2]
        try:
            callback_function(*row)
        except BaseException as e:
            print(index, row)
            traceback.print_exc()
    
    def run(self, iterable, callback_function,title=None):
        if not title:
            title = get_uuid(size=5)
        progress = Progress(len(iterable),title)
        for index,row in enumerate(iterable):
            process_args = (index,row,callback_function)
            self.jobs.append(process_args)
            if (index>0 and index%self.max_jobs==0) or index%(len(iterable)-1)==0:
                with Pool(self.max_jobs) as p:
                    p.map(self.callback_wrapper,self.jobs)
                progress.update(n=len(self.jobs))
                self.jobs = []

def test_multiprocess_manager():
    iterable = list(zip(range(100),range(10,110)))

    def test_process(a,b):
        print(a,b)
        time.sleep(2)

    point_cloud_segmentation = MultiprocessManager(max_jobs=8)
    point_cloud_segmentation.run(iterable, callback_function=test_process,title="Segmentation")


class MultiProcessManagerWithDataCollector():
    def __init__(self,max_jobs=12,json_storage_path="multiprocess_storage.json") -> None:
        self.max_jobs = max_jobs
        self.jobs = []
        manager = Manager()
        self.data_collector = manager.dict()
        self.storage = DictStorage(json_storage_path)

    def data_collection_wrapper(self,index,row,callback_function):
        try:
            self.data_collector[index] = callback_function(*row)
        except BaseException as e:
            print(index, row)
            traceback.print_exc()
    
    def run(self, iterable, callback_function,title=None):
        if not title:
            title = get_uuid(size=5)
        progress = Progress(len(iterable),title)
        for index,row in enumerate(iterable):
            process = Process(target=self.data_collection_wrapper, args=(index,row,callback_function))
            self.jobs.append(process)
            if (index>0 and index%self.max_jobs==0) or index%(len(iterable)-1)==0:
                for job in self.jobs:
                    job.start()
                # wait for all jobs to finish
                for job in self.jobs:
                    job.join()
                progress.update(n=len(self.jobs))
                self.jobs = []
                self.storage.multiple_update(self.data_collector)

        self.storage.save()