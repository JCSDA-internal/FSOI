#!/usr/bin/env python
##-----------------------------------------
import os
import sys
#
from pylab import *
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from argparse import ArgumentParser,ArgumentDefaultsHelpFormatter
#
parser = ArgumentParser(description = 'Plotting OmB Statistics Global',formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('-n','--nfile',help='No. of assimilated platforms',type=str,required=True)
parser.add_argument('-i1','--input1',help='Input file containing the filenames',type=str,required=True)
parser.add_argument('-i2','--input2',help='Input file containing the assimilated pltforms names',type=str,required=True)
parser.add_argument('-i3','--input3',help='Input file containing information about labels',type=str,required=True)
args = parser.parse_args()
#
nc = args.nfile
nc = int(nc)
cnt = nc - 1
print('No. of assimilated platforms = ' + str(nc))
#-------------------------------------------------------------------
#Reading input files
#-------------------------------------------------------------------
filepath = args.input1
platforms = args.input2
labels = args.input3
#
#--------Platform File
#
fp = open(platforms, 'r')
plat=[]
for line in fp:
        line = line.strip()
        plat.append(line)
fp.close()
#
i = 0
while (i <= cnt):
        print(plat[i])
        i += 1
#
#--------Labels
#
fp = open(labels, 'r')
lab=[]
for line in fp:
        line = line.strip()
        lab.append(line)
fp.close()
#
i = 0
while (i <= 4):
        print(lab[i])
        i += 1
#--------Statistics File
#
fp = open(filepath, 'r')
infile=[]
for line in fp:
        line = line.strip()
        infile.append(line)
fp.close()
#
hgt = {}
count = {}
bias = {}
rms = {}
countn = {}
i = 0
while (i <= cnt):
        print(infile[i])
        fp = open(infile[i], 'r')
        header = fp.readline()
        hgt[i] = []
        count[i] = []
        bias[i] = []
        rms[i] = []
#
        for line in fp:
                line = line.strip()
                columns = line.split()
                hgt[i].append(columns[0])
                count[i].append(columns[1])
                bias[i].append(columns[2])
                rms[i].append(columns[3])
#
        print(hgt[i])
        print(count[i])
        print(bias[i])
        print(rms[i])
#
#-------------------------------------------------------------------
#Plotting Line Graph
#-------------------------------------------------------------------
        font = {'family': 'serif',
                'color': 'black',
                'weight': 'normal',
                'style': 'italic',
                }
        clr = ['darkblue', 'darkgreen', 'red', 'cyan', 'magenta', 'purple', 'brown', 'orange', 'violet', 'pink', 'maroon', 'khaki', 'yellow', 'lime', 'gray']
#------------------------------------------
#Mean (O-B) Bias, RMS and Count.
        fig, ax = plt.subplots(figsize=(10, 8))
#
        p = str(plat[i])
        plt.plot(bias[i], hgt[i], color=clr[i], label='BIAS', linestyle='-', linewidth=3.0)
        plt.plot(rms[i], hgt[i], color=clr[i], label='RMS', linestyle='--', linewidth=3.0)
        plt.axvline(x=0, linestyle='--', color='black')
#
        ax.tick_params(direction='out')
        ax.xaxis.set_tick_params(labelsize=10)
        ax.yaxis.set_tick_params(labelsize=10)
        startx=-10
        endx=10
        ax.set_xlim(startx, endx)
        ax.xaxis.set_major_locator(MultipleLocator(2))
        ax.xaxis.set_minor_locator(MultipleLocator(1))
#
        ax.set_title(p + ': Diagnostics - PreQC ' + str(lab[4]) + '\n' + str(lab[1]) + ' - Global' + '\n', fontsize=16, fontdict=font)
        plt.xlabel('Mean Value(%)', fontsize=15, fontdict=font)
        plt.ylabel('Impact Height (km)', fontsize=15, fontdict=font)
#
#----------------------------------
        ax2 = ax.twiny()
        p = str(plat[i])
        countn = [float(j)/1000 for j in count[i]]
        print(countn)
        plt.plot(countn, hgt[i], color=clr[i], label='Count', linestyle=':', linewidth=3.0)
#
        plt.text(0.5, 0.98, 'Mean Count (in thousands)', color='black', fontsize=15, fontdict=font, horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
        ax2.xaxis.set_tick_params(labelsize=10)
        startx, endx = ax2.get_xlim()
        ax2.set_xlim([startx, endx])
        ax2.xaxis.set_ticks(np.arange(startx, endx, 0.1))
        for label in ax2.xaxis.get_ticklabels()[::2]:
                label.set_visible(False)
#
        starty=0
        endy=60
        ax.set_ylim(starty, endy)
        ax.yaxis.set_major_locator(MultipleLocator(5))
        ax.yaxis.set_minor_locator(MultipleLocator(2.5))
#
        plt.text(0.03, 0.2, 'COUNT ... (Dotted Line)', color='black', fontsize=12, fontdict=font, horizontalalignment='left', verticalalignment='center', transform=ax.transAxes)
        plt.text(0.03, 0.17, 'BIAS - (Solid Line)', color='black', fontsize=12, fontdict=font, horizontalalignment='left', verticalalignment='center', transform=ax.transAxes)
        plt.text(0.03, 0.14, 'RMS -- (Dashed Line)', color='black', fontsize=12, fontdict=font, horizontalalignment='left', verticalalignment='center', transform=ax.transAxes)
        plt.savefig(str(lab[3]) + '_diag_ihgt_PreQC_glb_' + p + '-' + str(lab[0]) + str(lab[2]))
#
        fp.close()
        i += 1
plt.close("all")
#------------------------------------------
