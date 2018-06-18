import time
from multiprocessing import Process

class my_work():
	"""docstring for my_work"""
	def __init__(self, value):
		self.value = [value]

	def work_add(self):
		while(self.value[0]<50):
			print('\nAddition is started\n')
			time.sleep(5)
			self.value[0] +=  1
			print("ADDED VALUE  %f" %self.value[0])
			print('\nAddition is ended\n')

	def value_print(self):
		while(self.value[0]<50):
			time.sleep(3)
			print("READ VALUE  %f" %self.value[0])

def main():
	working =my_work(2)
	if __name__=='__main__':
		value_get    = Process(target = working.value_print)
		value_change = Process(target = working.work_add)
	
		value_get.start()
		value_change.start()

		value_get.join()
		value_change.join()

	print ("\nWork Done\n")

main()