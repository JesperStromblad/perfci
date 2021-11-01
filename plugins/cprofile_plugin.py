from perfci.instrument_events import InstrumentEvents
import time
import sqlite3
from os.path import dirname, abspath
ROOT_DIR = dirname(dirname(abspath(__file__)))
import cProfile
from pstats import Stats
import os
## Plugin for Cprofile
class CProfileMeasurement(InstrumentEvents):

	def __init__(self,start_time):

		self.start_time = start_time

		super(CProfileMeasurement, self).__init__(self.start_time)


	def start_measurement(self):

		# Measuring time
		self.start_time = time.time()

		# Starting profiling calling context
		self.pr = cProfile.Profile()

		self.pr.enable()


	def end_measurement(self, *args):

		function_name = args[0]
		# Stop recording profile measurement
		self.pr.disable()

		# Take the time it took to run the unit test
		end_time = time.time() - self.start_time

		self.record_data(function_name, end_time , self.pr)



	def record_data(self, *args):

		# Storing the unit test profile data in the form of test name, unit test execution time and profile file

		# Name of the test
		test_func_name = args[0]


		# Execution time
		execution_time = args[1]

		# Profile data
		self.pr = args[2]
		self.pr.dump_stats('cprofile_plugin.'+test_func_name)

		cprofile_data = convertToBinaryData('cprofile_plugin.'+test_func_name)

		try:

			import os

			sqliteConnection = sqlite3.connect(os.getcwd()+'/perfci/plugins/database/cprofile_plugin.db')

			cursor = sqliteConnection.cursor()

			cursor.execute(
						   "insert into instrument (test_func_name, execution_time, cprofile_data) VALUES (?,?,?)",
						   [test_func_name, execution_time, cprofile_data]
						   )

			sqliteConnection.commit()

			cursor.close()


		except:
			import traceback
			traceback.print_exc()

		finally:
			if (sqliteConnection):

				sqliteConnection.close()

			print("The SQLite connection is closed")



# Utility method

def convertToBinaryData(filename):
	#Convert digital data to binary format
	with open(filename, 'rb') as file:
		blobData = file.read()
	return blobData



