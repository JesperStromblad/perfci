from perfci.plugins.counter import get_ids
from perfci.instrument_events import InstrumentEvents
import time
import os
from os.path import dirname, abspath
ROOT_DIR = dirname(dirname(abspath(__file__)))
import pulsar
import psutil
from statistics import mean
from githelper import get_short_commit_hash
import json

TOPIC = "RESOURCE_TOPIC"
PER_TEST_TOPIC = "PER_TEST_RESOURCE_TOPIC"

# Client object
client = pulsar.Client('pulsar://129.16.123.244:6650')
#client = pulsar.Client('pulsar://localhost:6650')
producer = client.create_producer(TOPIC)
test_producer = client.create_producer(PER_TEST_TOPIC)

TEST_SUITE_LENGTH = 65
mem_usage = []
total_unit_tests = 0
time_usage = []



unit_test_info = []
class ResourceCollection(InstrumentEvents):
    
    def __init__(self, start):
        self.start = 0
        super(ResourceCollection, self).__init__(self.start)
        
    def start_measurement(self):
            global total_unit_tests, mem_before
            total_unit_tests += 1
            
            self.start = time.time()
            
                
    def end_measurement(self, test_name):     
        global  total_unit_tests
        elapse_time = time.time() - self.start
        mem = self.get_process_memory()
        mem = int(mem)
        mem_usage.append(mem)
        time_usage.append(elapse_time)
        

        unit_test_info.append((test_name, elapse_time, mem))
        #unit_test_info.append((test_name, elapse_time))
        
        # Record the important information
        
        if total_unit_tests % TEST_SUITE_LENGTH == 0: 
                git_hash = get_short_commit_hash()
                avg_mem_usage =round(mean(mem_usage), 2)
                avg_time_usage = round(mean(time_usage), 5)
                self.record_data(git_hash, avg_mem_usage, avg_time_usage, unit_test_info)
                del mem_usage[:]
                del time_usage[:]
                del unit_test_info[:]


    def record_data(self, *args):
        global total_mem, total_et
        git_hash = str(args[0])
        mem = str(args[1])
        time = str(args[2])
        unit_test_data = str(args[3])
        
        data = json.dumps({"_key": get_ids(),
                           "git_commit": git_hash,
                           "avg_mem": mem,
                           "avg_time": time,
                           "unit_test_data": unit_test_data
                           })
        
        producer.send(data)
        #test_producer.send(unit_test_data )
    
    def get_process_memory(self):
         process = psutil.Process(os.getpid())
         return process.memory_info().rss   
