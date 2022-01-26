import numpy as np 
import yaml 
from tqdm.auto import tqdm
import pandas as pd 


class DAQSimulator:
	#config is a path to yaml configuration file with settings 
	def __init__(self, config):

		self.conf_path = config
		self.conf = None
		self.load_conf()


	def load_conf(self):
		#safe load yaml file 
		with open(self.conf_path, "r") as stream:
			try:
				self.conf = yaml.safe_load(stream)
			except yaml.YAMLError as exc:
				print("Problem loading yaml file:")
				print(exc)
