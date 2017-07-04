#!/usr/bin/python
import ROOT 
import skim 
import sys
import os
import loadoaAnalysisLib

####################################################################

class TPCMatchingSelector:
    '''Selects events suitable for TPC-TPC matching study'''

    def __init__(self):
        self.n_calls = 0
        self.n_selcted = 0

    def applySelection(self, event):

        self.n_calls+=1

        header     = event[('HeaderDir','BasicHeader')]
        dq         = event[('HeaderDir','BasicDataQuality')]
        tracker    = event[('ReconDir', 'Tracker' )] 
        trECal     = event[('ReconDir', 'TrackerECal' )]
        globalreco = event[('ReconDir', 'Global') ]


        magnet_off = dq.ND280OffFlag==1  and (dq.MAGNETFlag == 1 or dq.MAGNETFlag == -1)
        isMC = bool(ord(header.IsMC))
        if (not isMC) and not (dq.ND280OffFlag==0 or magnet_off):
            print "dq"
            return False 

        