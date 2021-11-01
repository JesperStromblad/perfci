from perfci.instrument_events import InstrumentEvents
import time
import sqlite3
from os.path import dirname, abspath
ROOT_DIR = dirname(dirname(abspath(__file__)))
from pyinstrument import Profiler,renderers
## Plugin for Cprofile
class StatisticalProfiler(InstrumentEvents):

	def __init__(self,start_time):

		self.start_time = start_time

		super(StatisticalProfiler, self).__init__(self.start_time)


	def start_measurement(self):

		# Measuring time
		self.start_time = time.time()

		# Starting profiling calling context

		self.pr = Profiler()

		self.pr.start()


	def end_measurement(self, *args):

		function_name = args[0]
		# Stop recording profile measurement
		self.pr.stop()

		# Take the time it took to run the unit test
		end_time = time.time() - self.start_time

		data = self.pr.output(renderers.JSONRenderer())


		self.record_data(function_name, end_time , data)



	def record_data(self, *args):

		# Storing the unit test profile data in the form of test name, unit test execution time and profile file

		# Name of the test
		test_func_name = args[0]


		# Execution time
		execution_time = args[1]

		# Profile data
		data = args[2]


		try:

			import os

			sqliteConnection = sqlite3.connect(os.getcwd()+'/perfci/plugins/database/statistical_profiler.db')

			cursor = sqliteConnection.cursor()

			cursor.execute(
						   "insert into instrument (test_func_name, execution_time, cprofile_data) VALUES (?,?,?)",
						   [test_func_name, execution_time, data]
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





