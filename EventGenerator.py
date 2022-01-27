import numpy as np 
import yaml 
from tqdm.auto import tqdm
import matplotlib.pyplot as plt 
import pandas as pd 

class EventGenerator:
        #config is a path to yaml configuration file with settings 
        def __init__(self, config):

                self.conf_path = config
                self.conf = None
                self.load_conf()

                #easy reference for columns of the output dataframe
                #desc:
                #nlappds_hit: number of lappds hit (for filtering)
                #lappds_hit: list of the lappd numbers hit, in case you want to compare distances.  
                #spill: the spill number, so that we don't have to count millions of microseconds, 
                #each timestamp references the beginning of the spill 
                cols = ["time", "nlappds_hit", "lappds_hit", "isnoise", "spill"]

                #output dataframe
                self.event_df = pd.DataFrame(columns=cols)

                #times of particles arriving at enclosure, detected or not
                self.particle_times = {} #spill number indexed, less compleixy than output df
                self.deadtime_endTimes = {}
                self.triggerMask = {}


        def load_conf(self):
                #safe load yaml file 
                with open(self.conf_path, "r") as stream:
                        try:
                                self.conf = yaml.safe_load(stream)
                        except yaml.YAMLError as exc:
                                print("Problem loading yaml file:")
                                print(exc)
                                self.conf = None

                self.daq_conf = self.conf["daq"] 
                self.conf = self.conf["events"] #just the events section


        def generate_particle_times(self, nspills):

                avg_rate = float(self.conf['beam_intensity'])/self.conf['spill_duration'] #Hz
                avg_dt = 1.0e6/avg_rate #microseconds between particles
                
                nparticles = int(float(self.conf['beam_intensity'])) #particles per spill

                triggerEff = float(self.conf["trigger_efficiency"])

                digiTime = float(self.daq_conf["digitization_time"])
                holdTime = float(self.daq_conf["trigger_hold_time"])

                # generatring particles for N spills, ignoring 53 MHz structure (shouldn't really matter all tha much) 
                for s in range(nspills):
                        startTimes = np.cumsum(np.random.exponential(avg_dt, nparticles))
                        # trigger should be handeled in deprate class
                        triggerMask = np.random.binomial(1, triggerEff, nparticles) == 1
                        self.triggerMask[s] = triggerMask
                        endTimes = startTimes + triggerMask*digiTime
                        endTimes[np.invert(triggerMask)] += holdTime
                        self.particle_times[s] = startTimes
                        self.deadtime_endTimes[s] = endTimes
                #working here still, not finished.
                


                        















