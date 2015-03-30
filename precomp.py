# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 10:17:05 2015

@author: lilei
"""
import sys
import re

# Version string
Version = "0.1"

# This controls whether info/debug messages are printed
# (0=none, 1=info, 2=info+debug)
DebugLevel = 1

def PRSetDebugLevel(level):
    global DebugLevel
    DebugLevel = level

def PRInfo( str ):
    global DebugLevel
    if DebugLevel >= 1:
        print >> sys.strdrr, str

def PRDebug( str ):
    global DebugLevel
    if DebugLevel >= 2:
        print >> sys.strdrr, str
        
def Fatal( str ):
	print >> sys.stderr, str
	sys.exit(-1)
 
class MIF:
    giPattern = re.compile(r'^([^\s]+)\s+.+')
    
    def __init__( self ):
        self.name = ""
        self.Bl_length = 0.0
        self.N_sections = 0
        self.N_materials = 0
        self.Out_format = 1
        self.TabDelim = True
        self.BssD = []
        self.WebsD = WEBS()
    
    def Load( self, file):
        with open(file) as pci:
            pci.readline()
            self.name = pci.readline()
            
            pci.readline()
            pci.readline()
            
            try:
                self.Bl_length  = float(self.ReadGeneralInformation( pci.readline()))
                self.N_sections  = int(self.ReadGeneralInformation( pci.readline()))
                self.N_materials  = int(self.ReadGeneralInformation( pci.readline()))
                self.Out_format  = int(self.ReadGeneralInformation( pci.readline()))
                self.TabDelim  = (self.ReadGeneralInformation( pci.readline()) == 't' and True) or False
            except Exception,ex:
                Fatal('General information Read error:' + ex.message)
            
            for i in range(7):
                pci.readline()
            
            for section in range(self.N_sections):
                bss = BSS(pci.readline())
                self.BssD.append(bss)
                
            for i in range(3):
                pci.readline()
                
            self.WebsD.Nweb = int(self.ReadGeneralInformation( pci.readline()))
            self.WebsD.Ib_sp_stn = int(self.ReadGeneralInformation( pci.readline()))
            self.WebsD.Ob_sp_stn = int(self.ReadGeneralInformation( pci.readline()))
            
            for i in range(2):
                pci.readline()
                
            for web in range(self.WebsD.Nweb):
                web_num = WEB_NUM(pci.readline())
                self.WebsD.Web_nums.append(web_num)
            
            
            
    def ReadGeneralInformation( self, line):
        try:
            match = self.giPattern.match(line)
            if match:
                return match.group(1)
            raise Exception('can not match the general information:' + line) 
        except Exception,ex:
            Fatal(ex.message)
        

class BSS:
    linePattern = re.compile(r'^([\d\.-]+)\s+([\d\.-]+)\s+([\d\.-]+)\s+([\d\.-]+)\s+\'(\S+)\'\s+\'(\S+)\'')
    
    def __init__( self, line):
        try:
            match = self.linePattern.match(line)
            if match:
                self.Span_loc = float(match.group(1))
                self.Le_loc = float(match.group(2))
                self.Chord = float(match.group(3))
                self.Tw_aero = float(match.group(4))
                self.Af_shape_file = match.group(5)
                self.Int_str_file = match.group(6)
            else:
                raise Exception('can not match the blade Sections Specific data:' + line) 
        except Exception,ex:
            Fatal(ex.message)        
        
class WEBS:
    def __init__( self):
        self.Nweb = 0
        self.Ib_sp_stn = 0
        self.Ob_sp_stn = 0
        self.Web_nums = []
        
class WEB_NUM:
    linePattern = re.compile(r'^(\d+)\s+([\d\.-]+)\s+([\d\.-]+).+')
    
    def __init__( self, line):
        try:
            match = self.linePattern.match(line)
            if match:
                self.Web_num = int(match.group(1))
                self.Inb_end_ch_loc = float(match.group(2))
                self.Oub_end_ch_loc = float(match.group(3))
            else:
                raise Exception('can not match the web data:' + line) 
        except Exception,ex:
            Fatal(ex.message)  
        
if __name__ == "__main__":
     mif = MIF()
     mif.Load('test01_composite_blade.pci')
     pass