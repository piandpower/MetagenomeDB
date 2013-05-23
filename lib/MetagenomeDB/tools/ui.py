
import sys

class progressbar:
	def __init__ (self, upper = None):
		self.__min = 0.0
		self.__max = upper + 0.0

	def display (self, value):
		f = (value - self.__min) / (self.__max - self.__min) # fraction
		p = 100 * f # percentage
		s = int(round(80 * f)) # bar size

		sys.stdout.write(' ' * 2 + ('.' * s) + " %4.2f%%\r" % p)
		sys.stdout.flush()

	def clear (self):
		sys.stdout.write(' ' * (2 + 80 + 8) + "\r")
		sys.stdout.flush()
