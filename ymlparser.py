"""
	This class parses yml ci files. It is used for modifying the base ci file based on the performance testing tasks defined.
	see https://gitlab.cern.ch/omjaved/perfci/-/wikis/Tutorial-for-running-automated-performance-testing-during-Continuous-Integration-(PERFCI)

"""
import errno
import os
from os.path import dirname, abspath
import oyaml as yaml
from collections import OrderedDict
from shutil import copyfile

"""Returns project root folder."""

ROOT_DIR = dirname(dirname(abspath(__file__)))

spec_file = ROOT_DIR + '/perfdata/VyPR_queries.py'

template_file = ROOT_DIR + '/perfdata/input_collection.py'


"""Main Parser class for parsing yml file"""
class Parser():

	def __init__(self):

		"""If ci files does not exist, we don't process"""
		if not (os.path.isfile(ROOT_DIR + '/.gitlab-ci.yml') or os.path.isfile(ROOT_DIR + '/.perf-ci.yml')):

			raise IOError(

				errno.ENOENT, os.strerror(errno.ENOENT), ROOT_DIR + '/.gitlab-ci.yml')

		self.origcifile = ROOT_DIR + '/.gitlab-ci.yml'

		self.perffile = ROOT_DIR + '/.perf-ci.yml'

		self.fail_fast = False

		self.resume = 0

		self.stop = 0

		self.plugin = None

		self.module_name = None

		self.custom_instructions = False

		self.verification = False

	def main_parser(self):

		"""Reading the ci file is a standard for both perf and normal ci file"""
		def read_cifile(ci_file):

			"""
			Reads the CI file
			:return:  dict containing yml keys and values
			"""
			with open(ci_file, 'r') as stream:
				try:
					ci_yml = yaml.safe_load(stream)
				except:
					import traceback
					traceback.print_exc()

			return ci_yml

		perf_file_contents = read_cifile(self.perffile)

		if 'performance' in perf_file_contents.keys():

			ci_file_contents = read_cifile(self.origcifile)

			is_stage_present = self.update_yml_value(ci_file_contents, 'stages')

			# Get all the keywords
			list_of_keywords = list(perf_file_contents.values())

			# Parse all the keywords and perform actions accordingly
			self.parsing_perf_ci_keys(list_of_keywords)

			self.add_vypr_instruction(is_stage_present)

	"""Update base CI file based on the actions defined in perf ci file"""
	def parsing_perf_ci_keys(self, keywords):
		"""
		:param keywords:	These are main keywords in the perf-ci.yml file
		"""

		fail_fast = False

		for item in keywords:

			if 'fail-fast' in item:
				if item['fail-fast'] == True:
					self.fail_fast = True


			if 'check-point' in item:
			#	if len(item['check-point']) > 1:
			#		print('Both resume and stop cannot be used at the same time')
			#		exit()


				if	len(item['check-point']) > 1:
					if 'resume' in item['check-point'][0]:
						self.resume = item['check-point'][0]['resume']
					elif 'resume' in item['check-point'][1]:
						self.resume = item['check-point'][1]['resume']


					if 'stop' in item['check-point'][1]:
						self.stop = item['check-point'][1]['stop']
					elif 'stop' in item['check-point'][0]:
						self.stop = item['check-point'][0]['stop']


					if self.resume == 0:
						print ('Resume cannot be zero. Only use stop if you want to start the initial input run')
						exit()

					if self.stop <= self.resume:
						print('Stop can be less or equal than resume. Select a higher number for stop')
						exit()

				else:
					if 'resume' in item['check-point'][0]:
						self.resume = item['check-point'][0]['resume']
					elif 'stop' in item['check-point'][0]:
						self.stop = item['check-point'][0]['stop']


			if 'unit-test-measurement' in item:

				plugin_type = item['unit-test-measurement'][0]['plugin']
				self.plugin = plugin_type
				dictionary = self.get_file_name(plugin_type)
				self.module_name = dictionary['file']
				self.module_name = self.module_name.replace('.py', '')

				path = dictionary['path']
				if not 'plugins' in path:
					self.custom_instructions = True



			if 'input-collection' in item:
				if 'script-path' in item['input-collection'][0]:
						path = item['input-collection'][0]['script-path']
						copyfile(path, template_file )
				else:
						# Generate a file used for performance analysis
						self.write_file(item['input-collection'])


			if 'performance-specification' in item:
				if not os.path.isfile(item['performance-specification'][0]):
					raise IOError(
						errno.ENOENT, os.strerror(errno.ENOENT), item['performance-specification'][0])

				# What to do with the path
				path = item['performance-specification'][0]
				copyfile(path, spec_file)
				self.verification = True


	"""Updates the file with VyPR instructions"""
	def add_vypr_instruction(self, is_stage_present):

		"""

		:param is_stage_present: checks if there is already a stage present in the base CI file
		"""

		with open(self.origcifile, 'r') as stream:
			try:
				ci_yml = yaml.safe_load(stream)
			except:
				import traceback
				traceback.print_exc()

			# get vypr instructions
			vypr_inst = self.vypr_instruction_dict(is_stage_present)

			# update the ci with VyPR instructions
			ci_yml.update(vypr_inst)

		if ci_yml:
			with open(self.origcifile,'w') as yamlfile:
				yaml.safe_dump(ci_yml, yamlfile)


	"""Adds Performance testing instructions in the base CI file"""
	def vypr_instruction_dict(self, is_stage_present):

		"""
		:param is_stage_present: checks if there is already a stage present in the base CI file
		:return:	OrderedDict
		"""

		fetch_repo_tuple = (
					 'apt-get update -qq && apt-get install -y -qq libsasl2-dev python-dev libldap2-dev libssl-dev tmux sqlite3 libsqlite3-dev sshpass alien libaio1',
					 'git clone https://github.com/JesperStromblad/cunit.git',
					 'export PYTHONPATH=\"$PYTHONPATH:.\"',
				 )

		if self.verification:
			verification_tuple = (

				'git clone https://github.com/JesperStromblad/VyPRServer.git',
				'cd VyPRServer/',
				'git checkout 33f3b4eb71e6139d0430a459736814652b41326e',
				'cd ..',
				'git clone https://github.com/JesperStromblad/VyPR.git',
				'cd VyPR/',
				'git checkout ca4bcb8fbddba560da34437b690cc4b1b7f8f44c',
				'cd ..',
				'mv perfdata/VyPR_queries.py .',
				'mv perfdata/vypr.config .',
				'cp -rf VyPR VyPRServer',
				'cd VyPRServer/',
				'tmux new -d -s verdict_server',
				'tmux send-keys -t verdict_server  \'pip install -r requirements.txt\' Enter;' ,
				'tmux send-keys -t  verdict_server  \'rm verdicts.db\' Enter;'
				'tmux send-keys -t  verdict_server \'sqlite3 verdicts.db < verdict-schema.sql\' Enter;',
				'tmux send-keys -t  verdict_server \'python run_service.py\' Enter;',
				'tmux send-keys -t  verdict_server \'sqlite3 verdicts.db < verdict-schema.sql\' Enter;',
				'tmux send-keys -t  verdict_server \'python run_service.py\' Enter;',
				'sleep 10',
				'tmux capture-pane -pt \'verdict_server\'',
				'cd ..',
				'python VyPR/instrument.py',

				)
		else:
			verification_tuple = ()

		if self.fail_fast:

			fail_fast_tuple = ('export FAILFAST=TRUE',)

		else:

			fail_fast_tuple = ()

		if (self.resume or self.stop) != 0:

			if self.resume > 0 and self.stop == 0:

				checkpoint_tuple = ('export RESUME='+str(self.resume),)

			elif self.stop > 0 and self.resume == 0:

				checkpoint_tuple = ('export STOP='+str(self.stop),)
			else:

				checkpoint_tuple = (
					                'export STOP='+str(self.stop),
									'export RESUME='+str(self.resume),
									)

		else:

			checkpoint_tuple = ()

		if self.plugin:

			plugin_tuple = (
				            'git clone https://gitlab.cern.ch/omjaved/perfci.git',
							'export PLUGIN=' + str(self.plugin),
							'export IMPORT=' + str(self.module_name),
							'export CUSTOM=' + str(self.custom_instructions),
							'python perfci/instrument.py',
							)

		else:

			plugin_tuple = ()

		vypr_run_tuple = (
							  'python perfdata/input_collection.py',
						)

		if self.verification:
			verdict_tuple = (

								'cp VyPRServer/verdicts.db perfdata/',

							)
		else:
			verdict_tuple = ()

		if self.plugin:

			data_tuple = (
						'cp perfci/plugins/database/'+str(self.module_name)+'.* perfdata/',
			)
		else:
			data_tuple = ()

		script = fetch_repo_tuple + verification_tuple  + fail_fast_tuple +  checkpoint_tuple + plugin_tuple + vypr_run_tuple + verdict_tuple +data_tuple


		if is_stage_present:

			return OrderedDict(

				performance_testing = OrderedDict(
					stage = 'performance_testing',
					#tags = ('latest',),
					script = script,
					artifacts = OrderedDict(
						paths = ('perfdata/*',),
						expire_in = ('1 week'),
					)

				)
			)
		else:

			return OrderedDict(

				stages = ('performance_testing',),
				performance_testing = OrderedDict(
					stage = 'performance_testing',
					#tags = ('latest',),
					script = script,
					artifacts = OrderedDict(
						paths = ('perfdata/*',),
						expire_in = ('1 week'),
					)
				)
			)

	"""writes to base CI file"""
	def write_file(self,code):
		with open (template_file, 'w') as file:
			file.write(code)

	"""Adds instruction for performance testing stage if it is not already present"""
	def update_yml_value(self, ci_file_contents, key, obj_value = 'performance_testing'):

		is_stage_present = False

		if key in ci_file_contents:

			is_stage_present = True

			if not 'performance_testing' in ci_file_contents[key]:

				stage_index = list(ci_file_contents).index(key)
				value = ci_file_contents[key]
				value.append(obj_value)
				ci_file_contents[ci_file_contents.keys()[stage_index]] = value

				with open(self.origcifile,'w') as yamlfile:
					yaml.safe_dump(ci_file_contents, yamlfile)

		return is_stage_present


	def get_file_name(self,class_name):

		import ast

		for r, d, f in os.walk(ROOT_DIR):
			for file in f:
				if file.endswith('.py'):
						file_path = r+'/'+file
						code = "".join(open(file_path, "r").readlines())
						asts = ast.parse(code)
						classes = [node.name for node in ast.walk(asts) if isinstance(node, ast.ClassDef)]
						if class_name in classes:
							return {'path': file_path, 'file':file}
		return None


"""
	Starting point for the running the yml parser
	Command to run -> python perfci/ymlparser.py to parse the base CI file.
	We run it in the root directory of the project.
	See instructions in the main page to understand how it works - https://gitlab.cern.ch/omjaved/perfci
"""

if __name__ == '__main__':

	parser = Parser()
	parser.main_parser()




