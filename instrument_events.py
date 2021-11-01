"This is the base class for unit test instrumentation plugins. This class can be extended for creating plugins"

from abc import ABCMeta,abstractmethod


class InstrumentEvents:

	"""The base class for all unit test instrumentation events"""



	__metaclass__ = ABCMeta

	def __init__(self, event):
		self.event = event


	@abstractmethod
	def start_measurement(self):
		pass

	@abstractmethod
	def end_measurement(self, *args):
		pass

	@abstractmethod
	def record_data(self):
		pass




