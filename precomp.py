# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 10:17:05 2015

@author: lilei
"""
import sys
import re
import math
import datetime

# Program name
ProgName = "precomp"
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
        print >> sys.stdout, str

def PRDebug( str ):
    global DebugLevel
    if DebugLevel >= 2:
        print >> sys.stdout, str
        
def Fatal( str ):
	print >> sys.stderr, 'Error',str
	sys.exit(-1)
 
def Warn( str ):
	print >> sys.stdout, 'Warning',str
 
class MIF:
    """Main input file class
    """
    __giPattern = re.compile(r'^([^\s]+)\s+.+')
    
    def __init__( self ):
        self.name = ""
        self.file_name = ""
        self.Bl_length = 0.0
        self.N_sections = 0
        self.N_materials = 0
        self.Out_format = 1
        self.TabDelim = True
        self.BssD = []
        self.WebsD = WEBS()
        self.Materials = []
        
        self.x1w = 0.0
        self.l_web = 0.0
        
        self.r1w = 0.0
        self.r2w = 0.0
        self.ch1 = 0.0
        self.ch2 = 0.0
    
    def LoadPci( self, file):
        with open(file) as pci:
            self.file_name = pci.name.split('.')[0]
            pci.readline()
            self.name = pci.readline()
            
            pci.readline()
            pci.readline()
            
            try:
                self.Bl_length  = float(self.__ReadGeneralInformation( pci.readline()))
                if self.Bl_length <= 0:
                    raise Exception('blade length not positive')
                    
                self.N_sections  = int(self.__ReadGeneralInformation( pci.readline()))
                if self.N_sections < 2:
                    raise Exception('number of blade stations less than two')
                    
                self.N_materials  = int(self.__ReadGeneralInformation( pci.readline()))
                
                self.Out_format  = int(self.__ReadGeneralInformation( pci.readline()))
                if self.Out_format <= 0 or self.Out_format > 3 :
                    raise Exception('out_format flag not recognizable')
                    
                self.TabDelim  = (self.__ReadGeneralInformation( pci.readline()) == 't' and True) or False
                                
            except Exception,ex:
                Fatal('General information Read error:' + ex.message)
            
            for i in range(7):
                pci.readline()
            
            #read blade-sections-specific data
            for section in range(self.N_sections):
                bss = BSS(pci.readline(), self.Bl_length)
                
                # check location of blade station
                if section == 0:
                    if abs(bss.Span_loc) > 0:
                        Fatal('first blade station location not zero')
                else:
                    if bss.Span_loc > self.Bl_length:
                        Fatal('blade station location exceeds blade length')
                    if bss.Span_loc < self.BssD[section-1].Span_loc:
                        Fatal('blade station location decreasing')
                        
                #check leading edge location
                if bss.Le_loc < 0:
                    Warn('leading edge aft of reference axis')
                
                #check chord length
                if bss.Chord <= 0:
                     Fatal('chord length not positive')
                
                self.BssD.append(bss)
            
            #get th_prime and phi_prime
            self.__tw_rate()
                   
            for i in range(3):
                pci.readline()
            
            try:
                self.WebsD.Nweb = int(self.__ReadGeneralInformation( pci.readline()))
                if self.WebsD.Nweb < 0:
                    raise Exception('negative number of webs')
                    
                if self.WebsD.Nweb == 0:
                    PRInfo('no webs in this blade')
                    self.WebsD.Webs_exist = 0
                    
                if self.WebsD.Nweb >= 1:
                    self.WebsD.Ib_sp_stn = int(self.__ReadGeneralInformation( pci.readline()))
                    if self.WebsD.Ib_sp_stn < 1:
                        raise Exception('web located inboard of the blade root')
                    
                    if self.WebsD.Ib_sp_stn > self.N_sections:
                        raise Exception('web inboard end past last blade stn')
                                                
                    self.WebsD.Ob_sp_stn = int(self.__ReadGeneralInformation( pci.readline()))
                    if self.WebsD.Ob_sp_stn < self.WebsD.Ib_sp_stn:
                        raise Exception('web outboard end location not past the inboard location')
                        
                    if self.WebsD.Ob_sp_stn > self.N_sections:
                        raise Exception('web outboard end past last blade stn')
                    else:
                        self.x1w = self.BssD[self.WebsD.Ib_sp_stn - 1].Span_loc
                        self.l_web = self.BssD[self.WebsD.Ob_sp_stn - 1].Span_loc - self.x1w
                    
                    #parameters required later for locating webs within a blade section
                    self.r1w = self.BssD[self.WebsD.Ib_sp_stn - 1].Le_loc
                    self.r2w = self.BssD[self.WebsD.Ob_sp_stn - 1].Le_loc
                    self.ch1 = self.BssD[self.WebsD.Ib_sp_stn - 1].Chord
                    self.ch2 = self.BssD[self.WebsD.Ob_sp_stn - 1].Chord
                    
                    for i in range(2):
                        pci.readline()
                
                    for web in range(self.WebsD.Nweb):
                        web_num = WEB_NUM(pci.readline())
                        if web == 0:
                            if web_num.Web_num != 1:
                                raise Exception('first web must be numbered 1')
                        else:
                            if web_num.Web_num != (web + 1):
                                raise Exception('web numbering not sequential')
                            if web_num.Inb_end_ch_loc < self.WebsD.Web_nums[web - 1].Inb_end_ch_loc:
                                raise Exception('webs crossing: not allowed currently')
                            if web_num.Oub_end_ch_loc < self.WebsD.Web_nums[web - 1].Oub_end_ch_loc:
                                raise Exception('webs crossing: not allowed currently')    
                                
                        self.WebsD.Web_nums.append(web_num)
            except Exception,ex:
                Fatal('Webs data Read error:' + ex.message)
                
            PRInfo('main input file read successfully')
            
           
    def LoadMaterials( self, file):
        with open(file) as inp:
            for i in range(3):
                inp.readline()
            for i in range(self.N_materials):
                material = Material(inp.readline())
                self.Materials.append(material)
        PRInfo('material read successfully')
                
            
    def __tw_rate( self):
        for section in range(1,self.N_sections - 1):
            f0 = self.BssD[section].Tw_aero
            f1 = self.BssD[section - 1].Tw_aero
            f2 = self.BssD[section + 1].Tw_aero
            h1 = self.BssD[section].Span_loc - self.BssD[section - 1].Span_loc
            h2 = self.BssD[section + 1].Span_loc - self.BssD[section].Span_loc
            self.BssD[section].th_prime = (h1*(f2-f0) + h2*(f0-f1))/(2.0*h1*h2)
        self.BssD[0].th_prime = (self.BssD[2].Tw_aero-self.BssD[1].Tw_aero)/(self.BssD[2].Span_loc-self.BssD[1].Span_loc)
        self.BssD[self.N_sections - 1].th_prime = (self.BssD[self.N_sections - 1].Tw_aero - self.BssD[self.N_sections - 2].Tw_aero)\
        /(self.BssD[self.N_sections - 1].Span_loc-self.BssD[self.N_sections - 2].Span_loc)
        
        for section in range(self.N_sections):
            self.BssD[section].phi_prime = 0.0
            self.BssD[section].tphip = self.BssD[section].th_prime + 0.5 * self.BssD[section].phi_prime
        
        
        
    def __ReadGeneralInformation( self, line):
        try:
            match = MIF.__giPattern.match(line)
            if match:
                return match.group(1)
            raise Exception('can not match the general information:' + line) 
        except Exception,ex:
            Fatal(ex.message)
        

class BSS:
    """Blade-sections-specific data class
    """
    __linePattern = re.compile(r'^([\d\.-]+)\s+([\d\.-]+)\s+([\d\.-]+)\s+([\d\.-]+)\s+\'(\S+)\'\s+\'(\S+)\'')
    
    def __init__( self, line, Bl_length):
        try:
            match = BSS.__linePattern.match(line)
            if match:
                self.Span_loc = float(match.group(1)) * Bl_length
                self.Le_loc = float(match.group(2))
                self.Chord = float(match.group(3))
                self.Tw_aero =  math.radians(float(match.group(4)))
                self.Af_shape_file = match.group(5)
                self.Int_str_file = match.group(6)
                
                self.th_prime = 0.0
                self.phi_prime = 0.0
                self.tphip = 0.0
                
            else:
                raise Exception('can not match the blade Sections Specific data:' + line) 
        except Exception,ex:
            Fatal(ex.message)        
        
class WEBS:
    """Webs (spars) data class
    """
    def __init__( self):
        self.Nweb = 0
        self.Webs_exist = 1
        self.Ib_sp_stn = 0
        self.Ob_sp_stn = 0
        self.Web_nums = []
        
class WEB_NUM:
    """Web data class
    """
    __linePattern = re.compile(r'^(\d+)\s+([\d\.-]+)\s+([\d\.-]+).+')
    
    def __init__( self, line):
        try:
            match = WEB_NUM.__linePattern.match(line)
            if match:
                self.Web_num = int(match.group(1))
                self.Inb_end_ch_loc = float(match.group(2))
                self.Oub_end_ch_loc = float(match.group(3))
            else:
                raise Exception('can not match the web data:' + line) 
        except Exception,ex:
            Fatal(ex.message)

class Material:
    """material property
    """
    __linePattern = re.compile(r'\s+(\d+)\s+([\d\.e+-]+)\s+([\d\.e+-]+)\s+([\d\.e+-]+)\s+([\d\.e+-]+)\s+([\d\.e+-]+).+')
    
    def __init__( self, line):
        try:
            match = Material.__linePattern.match(line)
            matdum = match.group(1)
            e1 = float(match.group(2))
            e2 = float(match.group(3))
            g12 = float(match.group(4))
            anu12 = float(match.group(5))
            self.density = float(match.group(6))
            
            if anu12 > math.sqrt(e1/e2):
                Warn(matdum + 'properties not consistent')
                
            anud = 1.0 - anu12*anu12*e2/e1
            self.q11 = e1/anud
            self.q22 = e2/anud
            self.q12 = anu12*e2/anud
            self.q66 = g12
            
        except Exception,ex:
            Fatal(ex.message)

class ASF:
    '''airfoil geometry
    '''
    __nsPattern = re.compile(r'^([^\s]+)\s+.+')
    __nodeXYPattern = re.compile(r'^([\d\.eE+-]+)\s+([\d\.eE+-]+).*')
    
    def __init__( self, file):
        try:
            with open(file) as asf:
                self.n_af_nodes = int(self.__ReadNodesNum(asf.readline()))
                self.nodes_u = 0
                self.xnode_u = []
                self.ynode_u = []
                self.nodes_l = 0
                self.xnode_l = []
                self.ynode_l = []
                self.xnode = [0] * self.n_af_nodes
                self.ynode = [0] * self.n_af_nodes
                for i in range(3):
                    asf.readline()
                    
                if self.n_af_nodes <= 2:
                    raise Exception('min 3 nodes reqd to define airfoil geometry')
                
                for node in range(self.n_af_nodes):
                    self.xnode[node],self.ynode[node] = self.__ReadNodeXY(asf.readline())
        except Exception,ex:
            Fatal(ex.message)
            
    def __ReadNodesNum( self, line):
        try:
            match = ASF.__nsPattern.match(line)
            if match:
                return match.group(1)
            raise Exception('can not match the general information:' + line) 
        except Exception,ex:
            Fatal(ex.message)

    def __ReadNodeXY( self, line):
        try:
            match = ASF.__nodeXYPattern.match(line)
            if match:
                return (float(match.group(1)), float(match.group(2)))
            raise Exception('can not match the general information:' + line) 
        except Exception,ex:
            Fatal(ex.message)
    
    def CheckFirstNode(self):
        location = self.xnode.index(min(self.xnode))
        if location != 0:
            Fatal('the first airfoil node not a leading node')
        
        if self.xnode[0] != 0 or self.ynode[0] != 0 :
            Fatal('leading-edge node not located at (0,0)')

    def IdentifyTrailingEdge(self):
        location = self.xnode.index(max(self.xnode))
        if self.xnode[location] > 1:
            Fatal('trailing-edge node exceeds chord boundary')
        
        tenode_u = location
        ncounter = 0
        for i in range(location, self.n_af_nodes):
            if abs(self.xnode[i] - self.xnode[location]) == 0:
                ncounter = i - location
        tenode_l = tenode_u + ncounter
        
        if ncounter > 0:
            PRInfo('blunt te identified between airfoil nodes %d and %d' % (tenode_u,tenode_l))
        
        self.nodes_u = tenode_u
        self.xnode_u = [0] * self.nodes_u
        self.ynode_u = [0] * self.nodes_u
        self.nodes_l = self.n_af_nodes - tenode_l + 2
        self.xnode_l = [0] * tenode_l
        self.ynode_l = [0] * tenode_l
        
        
        for i in range(self.nodes_u):
            self.xnode_u[i] = self.xnode[i]
            self.ynode_u[i] = self.ynode[i]
        
        self.xnode_l[0] = self.xnode[0]
        self.ynode_l[0] = self.ynode[0]
        
        for i in range(1,tenode_l):
            self.xnode_l[i] = self.xnode[self.n_af_nodes-i]
            self.ynode_l[i] = self.ynode[self.n_af_nodes-i]
    
def BuildOutFile(mifObject):
    OutFile_gen = '%s.out_gen' % (mifObject.file_name)
    OutFile_bmd = '%s.out_bmd' % (mifObject.file_name)
    if mifObject.Out_format != 2:
        with open(OutFile_gen,'w') as gen:
            cutoff = '====================================\
==============================================\n'
            gen.write(cutoff)
            gen.write('Results generated by %s %s on %s.\n' % (ProgName, Version, datetime.datetime.now()))
            gen.write('%s\n' % mifObject.name)
            gen.write(cutoff)
            gen.write('\n')
            gen.write('  blade length (meters) =%7.2f\n\n' % mifObject.Bl_length)
            delim = '\t'
            if not mifObject.TabDelim:
                delim = '   '
                gen.write('  ')
            gen.write('span_loc%schord%stw_aero%sei_flap%sei_lag%sgj%sea%ss_fl%ss_af%ss_al%s\
s_ft%ss_lt%ss_at%sx_sc%sy_sc%sx_tc%sy_tc%smass%sflap_iner%slag_iner%stw_iner%sx_cm%sy_cm\n' % tuple((delim,) * 22))
            gen.write('     (-)%s(m)%s(deg)%s(Nm^2)%s(Nm^2)%s(Nm^2)%s(N)%s(Nm^2)%s(Nm)%s(Nm)%s\
(Nm^2)%s(Nm^2)%s(Nm)%s(m)%s(m)%s(m)%s(m)%s(Kg/m)%s(Kg-m)%s(Kg-m)%s(deg)%s(m)%s(m)\n' % tuple(('   ',) * 22))
    if mifObject.Out_format != 1:
        with open(OutFile_bmd,'w') as bmd:
            cutoff = '====================================\
==============================================\n'
            bmd.write(cutoff)
            bmd.write('Results generated by %s %s on %s.\n' % (ProgName, Version, datetime.datetime.now()))
            bmd.write('%s\n' % mifObject.name)
            bmd.write(cutoff)
            bmd.write('\n')
            bmd.write('  blade length (meters) =%7.2f\n\n' % mifObject.Bl_length)
            delim = '\t'
            if not mifObject.TabDelim:
                delim = '   '
                bmd.write('  ')
            bmd.write('span_loc%sstr_tw%stw_iner%smass_den%sflp_iner%sedge_iner%s\
flp_stff%sedge_stff%stor_stff%saxial_stff%scg_offst%ssc_offst%stc_offst' % tuple((delim,) * 12))
            bmd.write('   (-)%s(deg)%s(deg)%s(kg/m)%s(kg-m)%s(kg-m)%s(Nm^2)%s\
(Nm^2)%s(Nm^2)%s(N)%s(m)%s(m)%s(m)' % tuple(('   ',) * 12))
            
    PRInfo('general out_format successfully')

        
if __name__ == "__main__":
     mif = MIF()
     mif.LoadPci('test01_composite_blade.pci')
     mif.LoadMaterials('materials.inp')
     BuildOutFile(mif)
     #begin blade sections loop
     PRInfo('begin blade sections loop')
     for iaf in range(mif.N_sections):
         PRInfo('BLADE STATION %d analysis begins' % (iaf+1))
         
         ch = mif.BssD[iaf].Chord
         rle = mif.BssD[iaf].Le_loc
         
         asf = ASF(mif.BssD[iaf].Af_shape_file)
         asf.CheckFirstNode()
         asf.IdentifyTrailingEdge()
         
         
         PRInfo('BLADE STATION %d analysis ends' % (iaf+1))
             
     
     