"""

Instruments unit tests which is done to support plugin.
see https://gitlab.cern.ch/omjaved/perfci/-/wikis/Custom-plugins

"""

import time
import ast
import py_compile
import marshal
from os.path import dirname, abspath

ROOT_DIR = dirname(dirname(abspath(__file__)))

class InstrumentUnitTest:


	"""This function handles all the instrumentation related task such as passes the python bytecode to necessary methods"""

	@staticmethod
	def instrument_feedback(module_list, plugin_type, import_module, custom_module):

		"""

		:param module_list: Takes a module list to instrument
		:param plugin_type: Type of plugin defined in the performance testing task config file
		:param import_module: Module to import based on the name of the python file
		:param custom_module: In case of custom plugin
		:return:
		"""


		for module in module_list:
			if module.endswith('.py'):
				ext = '.py'
			elif module.endswith('.inst'):
				ext = '.py.inst'

			file_name = module
			file_name_without_extension = module.replace(ext, "")


			# extract asts from the code in the file
			code = "".join(open(file_name, "r").readlines())
			asts = ast.parse(code)

			for node in asts.body:
				if type(node) == ast.ClassDef:
					class_name = node.name

			create_setup_method(asts.body, class_name, plugin_type, import_module, custom_module)

			create_teardown_method(asts, class_name)


			# compile bytecode
			compile_bytecode_and_write(asts,file_name_without_extension, ext)




"""This function adds setup method in the test class"""
def create_setup_method(current_step, class_name,plugin_type,import_module, custom_module):
	"""
	:param current_step:            Contains the AST for the code
	:param class_name:              Name of the test class
	:param plugin_type				Type of the plugin
	:param import_module			Module to import based on the name of the python file
	:
	"""

	setUp_found = False

	## Finding the test class.
	current_step = filter( lambda entry: (type(entry) is ast.ClassDef and
										  entry.name == class_name), current_step)[0]


	test_class_body = current_step.body


	#impt = "from perfci.plugins.unit_test_time import UnitTestTimeMeasurement"
	if custom_module == 'True':
		dictionary = get_file_name(plugin_type)

		import_module = dictionary['file']
		path = dictionary['path']

		import_module = import_module.replace('.py', '')

		import shutil
		shutil.copy(path, ROOT_DIR+'/perfci/plugins/')

		file_list = get_all_file_name(import_module)
		for file in file_list:
			shutil.copy(file, ROOT_DIR+'/perfci/plugins/database/')



	impt = "from perfci.plugins."+import_module+ ' import ' + plugin_type
	obj_statement = "self.measurement ="+ plugin_type + "(0)"
	measure_statement = "self.measurement.start_measurement()"


	for test_function in test_class_body:

		if not (type(test_function) is ast.FunctionDef):
			continue

		if test_function.name == 'setUp':

			setUp_found = True

			setup_transaction = ast.parse(impt).body[0]
			statement_add = ast.parse(obj_statement).body[0]
			measure_add = ast.parse(measure_statement).body[0]
			test_function.body.insert(0,setup_transaction)
			test_function.body.insert(1,statement_add)
			test_function.body.insert(2,measure_add)


	# If there is no setUpClass method, then we need to add setUp method in the class.
	if not setUp_found:
		setUp_method = "def setUp(self):\n\t" + impt + "\n\t" + obj_statement + "\n\t" + measure_statement

		method_inst = ast.parse(setUp_method).body[0]
		test_class_body.insert(0,method_inst)



"""This function adds teardown method in the test class"""
def create_teardown_method(ast_code, class_name):

	"""
	:param ast_code:            Code for the AST
	:param class_name:          Class name
	"""


	tearDown_found = False

	statement = "self.measurement.end_measurement(self._testMethodName)"

	## Finding the test class.
	current_step = filter( lambda entry: (type(entry) is ast.ClassDef and
										  entry.name == class_name), ast_code.body)[0]

	test_class_body = current_step.body


	for test_function in test_class_body:

		if not (type(test_function) is ast.FunctionDef):
			continue

		if test_function.name is 'tearDown':
			# We found tearDown method, now we need to add verification instructions
			tearDown_found = True
			verification_call_inst = ast.parse(statement).body[0]
			test_function.body.insert(0,verification_call_inst)


	if not tearDown_found:
		tear_method = "def tearDown(self):\n\t" + statement
		method_inst = ast.parse(tear_method).body[0]
		test_class_body.insert(len(test_class_body),method_inst)


"""Compile ASTs to bytecode then write to file.  The method we use depends on the Python version."""
def compile_bytecode_and_write(asts, file_name_without_extension, ext):

	"""

	:param asts: File in AST code
	:param file_name_without_extension: To create a temporary file in order for python interpreter to run .pyc file
	:param ext: Extension to decide where to modify .py or .py.inst
	"""


	backup_file_name = "%s.py.inst" % file_name_without_extension

	instrumented_code = compile(asts, backup_file_name, "exec")

	# append an underscore to indicate that it's instrumented - removed for now
	instrumented_file_name = "%s%s" % (file_name_without_extension, ".pyc")

	import struct

	with open(instrumented_file_name, "wb") as h:
		h.write(py_compile.MAGIC)
		py_compile.wr_long(h, long(time.time()))
		# the write operation is the same regardless of Python version
		marshal.dump(instrumented_code, h)

	if ext.endswith('.py'):
		os.rename("%s.py" % file_name_without_extension, "%s.py.inst" % file_name_without_extension)



""" Get the name of the python file for instrumentation"""
def get_file_name(class_name):

	"""

	:param class_name: Name of the class
	:return: a dictionary containing path and file name
	"""

	import ast

	for r, d, f in os.walk(ROOT_DIR):
		for file in f:
				if file.endswith('.py'):
					file_path = r+'/'+file
					code = "".join(open(file_path, "r").readlines())
					asts = ast.parse(code)
					classes = [node.name for node in ast.walk(asts) if isinstance(node, ast.ClassDef)]
					if class_name in classes:
						return {'path':file_path, 'file':file}


	return None


"""Get a list of all file names based on the name provided"""
def get_all_file_name(name):

	"""
	:param name: Name of the file
	:return: list of complete path of the file
	"""

	file_list = []
	#for r, d, f in os.walk(os.environ('PATH')):
	for r, d, f in os.walk(ROOT_DIR):
		for file in f:
			if not file.endswith('.py'):
				if name in file:
					file_list.append(r+'/'+file)

	return file_list

"""To run the instrumentation process based on the environment variables supplied from the CI process"""
if  __name__ == '__main__':


	import os

	if "CUSTOM" in os.environ:
		c_module = os.environ['CUSTOM']
	else:
		c_module = 'False'

	module_path = []

	path = ROOT_DIR+'/test'

	#for r, d, f in os.walk(os.environ('PATH')):
	for r, d, f in os.walk(path):
		for file in f:
			if file.startswith("test_") and (file.endswith('.py') or file.endswith('.py.inst')):
				module_path.append(os.path.join(r, file))



	InstrumentUnitTest.instrument_feedback(
		module_path,
		plugin_type 	= os.environ['PLUGIN'],
		import_module 	= os.environ['IMPORT'],
		custom_module 	= c_module
		)


