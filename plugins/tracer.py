# TODO: Return values from each function and output of the test case as a feature

from perfci.instrument_events import InstrumentEvents
import time
import sqlite3
import os
from os.path import dirname, abspath
import sys
ROOT_DIR = dirname(dirname(abspath(__file__)))
import pulsar
from collections import OrderedDict
from githelper import get_short_commit_hash
from perfci.plugins.counter import get_ids
import json
trace_list_test_case = []
input_trace_list = []
list_test_cases = []
complete_input_trace = False
time_info = None

#Encoding 
conditional_encode_dict = OrderedDict()
return_encode_dict = OrderedDict()


# Exclude test files and instrumentation files from tracing
EXCLUSION_LIST = ["site-packages", "python", "tracer", "test", "<string>"]

TEST_NAME_EXCLUSION = ["get_test_session_id", "environ"]
#TOPIC

TOPIC = "TRACE_TOPIC"
TEST_CASE_TOPIC= "PER_TEST_CASE_TOPIC"
# Client object
client = pulsar.Client('pulsar://129.16.123.244:6650')
#client = pulsar.Client('pulsar://localhost:6650')
producer = client.create_producer(TOPIC)

test_case_producer = client.create_producer(TEST_CASE_TOPIC)

TEST_SUITE_LENGTH = 65 

INPUT_FILE=os.getcwd()+'/perfci/plugins/script/conditionals_info'

data_dict = {}  

# Input data per test suite
input_data = []
        
# For storing function calls, no statements 
function_calls = []
no_statements_executed = 0
        
# For storing conditional and return value information
conditional_list = []
no_iterations = 0
return_value_list = []
return_values = None
call_counter = 0
        
# unit test related information
test_case_list = []
executed_unit_tests = []
total_unit_tests = 0
lenght_unit_tests = 0
test_list_identified = False

## Total stats
total_function_calls = 0
total_no_statements_executed = 0
total_no_iterations = 0


# Per test case Information
per_test_function_call = []
executed_line_no = []
per_test_iterations = 0
per_test_conditional = []
unit_test_info = []

class ExecutionTrace(InstrumentEvents):

    def __init__(self,start_time):
             
        self.start_time = start_time

        super(ExecutionTrace, self).__init__(self.start_time)


    def trace_lines(self,frame, event, arg):
        """

        :param frame:
        :param event:
        :param arg:
        :return:
        """
        global no_statements_executed, return_values
        co = frame.f_code

        func_name = co.co_name

        line_no = frame.f_lineno

        full_filename = co.co_filename

        if event == 'return':
            return
               
        # No of statements executed
        no_statements_executed += 1
    
        # per test executed line numbers
        executed_line_no.append(line_no)
           
        # Num of iterations
        self.conditional_check(full_filename, line_no)
        


    def trace_calls(self,frame, event, arg):
        """

        :param frame:
        :param event:
        :param arg:
        :return:
        """

        global total_unit_tests, test_case_list
        
        #   Getting the frame object
        co = frame.f_code
        
        # Getting the full file name information
        full_filename = co.co_filename
        
        # Function names stored as a list
        function_name = frame.f_code.co_name
        
        # Only unit test cases are stored in list
        if 'test'in function_name and 'test' in full_filename and not any(test_name in str(function_name) for test_name in TEST_NAME_EXCLUSION):
            
            total_unit_tests += 1      # Count number of unit tests
            test_case_list.append(function_name)
            # Check for unit test lenght
            #self.identify_testsuite_length(function_name)       
            
                
                
        # If the event is not a call or there is any package from exclusion list we don't trace.
        if event != 'call' or any(package in str(full_filename) for package in EXCLUSION_LIST):
            return
        

        # Save assumption for junit test in python. You need to have test in test case name                 
        function_calls.append(function_name)
        per_test_function_call.append(function_name)
                  
        return self.trace_lines
    

    def start_measurement(self):
        return sys.settrace(self.trace_calls)

    def end_measurement(self, test_obj):

        global total_unit_tests,  no_statements_executed, total_function_calls, total_no_statements_executed, total_no_iterations, return_values, per_test_iterations
        test_name = test_case_list.pop()
        # Storing the result of test case
        result = 0 if None in sys.exc_info() else 1     
        
        total_function_calls += len(function_calls)
        del function_calls [:]
        total_no_statements_executed += no_statements_executed
        total_no_iterations += no_iterations

        
        # Per test data
        test_func_calls = len(per_test_function_call)
        line_numbers = len(executed_line_no)
        encode_per_test_cond = encode_sequence_conditional(str(per_test_conditional))
        unit_test_info.append((test_name, test_func_calls, line_numbers, per_test_iterations, encode_per_test_cond, result))
        
        per_test_iterations = 0
        del per_test_function_call[:]
        del executed_line_no[:]
        del per_test_conditional[:]
        
        
        # input_data.append((test_name, 
        #                 function_calls, 
        #                 no_statements_executed, 
        #                 conditional_encode_value, #conditional_list, 
        #                 no_iterations, 
        #                 return_encode_value, #return_value_list, 
        #                 result))
        
        # Record the important information
        if total_unit_tests % TEST_SUITE_LENGTH == 0:
           
            conditional_encode_value = encode_sequence_conditional(str(conditional_list))
            #return_encode_value = None
            return_encode_value = encode_sequence_return_list(return_values)
            
            
            self.record_data(str(total_function_calls), 
                             str(total_no_statements_executed),
                            str(conditional_encode_value),
                            str(total_no_iterations),
                            str(unit_test_info)
                            )
                
        
            self.cleanUp()
        
        return sys.settrace(None)

    def record_data(self,*args):
        
            git_hash = get_short_commit_hash()
            
            # trace = args[0] + ',' + args[1] +','+ args[2] +','+ args[3]
            # test_case_data = args[4]
        
            data = json.dumps({"_key": get_ids(),
                           "git_commit": git_hash,
                           "total_function_calls": args[0],
                           "total_no_statements_executed": args[1],
                           "conditional_encode_value": args[2],
                           "total_no_iterations": args[3],
                           "unit_test_data": args[4]
                           
                           })
        
        
            producer.send(data)
            #test_case_producer.send(test_case_data)
            
        
    def cleanUp(self):
            global  no_statements_executed, no_iterations, total_no_statements_executed, total_no_iterations, total_function_calls, return_values
            del function_calls [:]
            del conditional_list[:]
            del return_value_list[:]
            del unit_test_info[:]
            no_statements_executed = 0
            no_iterations = 0
            total_no_statements_executed = 0
            total_function_calls = 0
            total_no_iterations = 0
            return_values = None


    def create_dictionary(self):
   
        file = open (INPUT_FILE)
        for line in file:
            key, value = line[:-1].split(",")
            self.data_dict [key] = value
    

    def get_conditional_info(self):
        import subprocess, os
        subprocess.call(os.getcwd()+"/perfci/plugins//script/branch_identification.sh")

    def conditional_check(self,full_filename, line_no):
        global no_iterations, per_test_iterations

        # No of divergence points
        file_info = full_filename+":"+str(line_no)
        if file_info in data_dict:
            
            if 'if' in data_dict[file_info] or 'elif' in data_dict[file_info].replace(' ', '') or 'else' in data_dict[file_info].replace(' ', ''):
                conditional_list.append(data_dict[file_info])
                per_test_conditional.append(data_dict[file_info])
            elif 'for' in data_dict[file_info].replace(' ', ''):
                no_iterations +=1
                per_test_iterations +=1        
                
                
def create_dictionary():
       
        file = open (INPUT_FILE)
        for line in file:
            key, value = line[:-1].split(",")
            data_dict [key] = value
    

def get_conditional_info():
        import subprocess, os
        subprocess.call(os.getcwd()+"/perfci/plugins//script/branch_identification.sh")
        

## Get integer values for same sequence (simple encoding)
def encode_sequence_conditional(value):
    if value in conditional_encode_dict.keys():
        return conditional_encode_dict[value]
    else:
        # If dictionary not empty
        if bool(conditional_encode_dict):
            last_item = conditional_encode_dict.keys()[-1]
            stored_encode_value = conditional_encode_dict[last_item]
            stored_encode_value +=1
            conditional_encode_dict[value] = stored_encode_value
            return stored_encode_value
        # If dictionary is empty
        else:
            conditional_encode_dict [value] = 1 
            return 1   

def encode_sequence_return_list(value):
    if value in return_encode_dict.keys():
        return return_encode_dict[value]
    else:
        # If dictionary not empty
        if bool(return_encode_dict):
            last_item = return_encode_dict.keys()[-1]
            stored_encode_value = return_encode_dict[last_item]
            stored_encode_value +=1
            return_encode_dict[value] = stored_encode_value
            return stored_encode_value
        # If dictionary is empty
        else:
            return_encode_dict [value] = 1   
            return 1 

        
get_conditional_info()
        
# For storing static locations of conditionals
create_dictionary()  