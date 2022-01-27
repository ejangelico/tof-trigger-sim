import numpy as np 
import yaml 
from tqdm.auto import tqdm
import pandas as pd 
import numba

class LAPPDStation:
    #config is a path to yaml configuration file with settings 
    def __init__(self, config):
        
        self.conf_path = config
        self.conf = None
        self.load_conf()

        #times of particles arriving at enclosure, detected or not
        self.noise_times = {} #spill number indexed, less compleixy than output df
        self.deadtime_endTimes = {}

    def load_conf(self):
        #safe load yaml file 
        with open(self.conf_path, "r") as stream:
            try:
                self.conf = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print("Problem loading yaml file:")
                print(exc)

        self.daq_conf = self.conf["daq"]
        self.conf = self.conf["events"] #just the events section

    def generate_noise_times(self, nspills):
        
        avg_rate = float(self.conf['noise_rate'])

        avg_dt = 1.0e6/avg_rate #microseconds between particles
                
        nNoise = int(avg_rate*float(self.conf['spill_duration'])) #average noise eventsper spill 
        holdTime = float(self.daq_conf["trigger_hold_time"])
        
        # generatring noise for N spills
        for s in range(nspills):
            # we can't predict exact number of events needed so generate a few more and chop off extras
            self.noise_times[s] = np.cumsum(np.random.exponential(avg_dt, nNoise + 2))
            self.noise_times[s] = self.noise_times[s][self.noise_times[s] < 1e6*self.conf['spill_duration']] 
            #Currently assuming that noise never causes "global" trigger, can udpate later, but should have small effect 
            self.deadtime_endTimes[s] = self.noise_times[s] + holdTime

    @staticmethod
    @numba.jit(nopython=True)
    def reconciliation(times, deadTimes, acceptMask):
        iDeadTime = 0;
        for iTime in range(1, len(times)):
            if times[iTime] < deadTimes[iDeadTime]:
                acceptMask[iTime] = False
            else:
                iDeadTime = iTime
            
    def reconcile_times(self, evtGen, nspills):

        self.allTimes = {}
        self.allDeadTimes = {}
        self.eventClass = {}
        self.acceptMasks = {}
        self.passTrigger = {}
        for s in range(nspills):
            self.allTimes[s] = np.concatenate( (evtGen.particle_times[s], self.noise_times[s]) )
            self.allDeadTimes[s] = np.concatenate( (evtGen.deadtime_endTimes[s], self.deadtime_endTimes[s]) )
            self.eventClass[s] = np.concatenate( (np.full((len(evtGen.particle_times[s])), 1), np.full((len(self.noise_times[s])), 2)) )
            self.passTrigger[s] = np.concatenate( (evtGen.triggerMask[s], np.full((len(self.noise_times[s])), False)) )
            #resort arrays by event time 
            args = np.argsort(self.allTimes[s])
            self.allTimes[s]  = self.allTimes[s][args]
            self.allDeadTimes[s] = self.allDeadTimes[s][args]
            self.eventClass[s]  = self.eventClass[s][args]
            self.passTrigger[s] =self.passTrigger[s][args]

            #Is there a way to do this operation in a vectorized way??
            acceptMask = np.full(len( self.allTimes[s]), True)
            self.reconciliation(self.allTimes[s], self.allDeadTimes[s], acceptMask)
            self.acceptMasks[s] = acceptMask
