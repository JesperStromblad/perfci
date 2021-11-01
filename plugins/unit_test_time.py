from perfci.instrument_events import InstrumentEvents
import time
import sqlite3
from os.path import dirname, abspath
ROOT_DIR = dirname(dirname(abspath(__file__)))


class UnitTestTimeMeasurement(InstrumentEvents):

	def __init__(self,start_time):

		self.start_time = start_time

		super(UnitTestTimeMeasurement, self).__init__(self.start_time)


	def start_measurement(self):

			self.start_time = time.time()

	def end_measurement(self, *args):

			function_name = args[0]

			end_time = time.time() - self.start_time

			self.record_data(function_name, end_time)
			#self.record_data(end=end_time)


	def record_data(self, *args):

		test_func_name = args[0]
		execution_time = args[1]

		try:


			import os
			sqliteConnection = sqlite3.connect(os.getcwd()+'/perfci/plugins/database/unit_test_time.db')

			cursor = sqliteConnection.cursor()

			cursor.execute("insert into instrument (test_func_name, execution_time) VALUES (?,?)",
						   [test_func_name, execution_time])


			sqliteConnection.commit()

			cursor.close()


		except:
			import traceback
			traceback.print_exc()

		finally:
			if (sqliteConnection):

				sqliteConnection.close()

			print("The SQLite connection is closed")


#unit = UnitTestTimeMeasurement(0)
#unit.record_data('method1', 1)