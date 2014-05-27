import glob
import composite
import Plotting
from astropy.table import Table
from astropy.io import ascii
import matplotlib.pyplot as plt
import numpy as np

import sqlite3 as sq3
from scipy import interpolate as intp
import math
import msgpack as msg
import msgpack_numpy as mn
from prep import *
from datafidelity import *

"""
*Meant to be used from src folder

This code is designed to check each spectra file, one by one, given a particular source,
by plotting the original and the interpolated spectra together, along with the 
inverse varience.  

comments can be given to note telluric absorption, errors in reddening, spikes in fluxes,
clipping, or any other problems with either the original or interpolated spectra
"""

"""
ROUGH OUTLINE OF CODE
-select SOURCE (bsnip,cfa,csp,other,uv)
-pull all FILENAMES from selected source
-select START index [0 to (len(source)-1))]

MAIN LOOP:	
	-read data at index (from START)
	-create separate interpolated data INTERP
	-get inverse varience values INVAR
	-plot ORIG and INTERP data 
	 with INVAR
	-Observe and Comment:
		-[enter](blank input)
		 	plot is fine(don't add to list)
		-type comment(telluric, spikes, etc...)
		 	added to 2 column list-> |FILENAME|COMMENT|
		-'q' or 'quit' to end, saves ending index END
	-Continues onto next file

	When Quitting:
		save list to file in format: 
		('SOURCE_'+'START'+'_'+'END')
		ex. ('cfa_0_200.dat')

===========
guidelines:
===========
[ ] - need to implement
[x] - implemented

#comment on the functionality of the blocks of code
##commented out code that does checks on the functionality of code
==========
variables: (work in progress)
==========
SOURCE		which source data is being looked at(bsnip,cfa,etc.)
FILENAMES	path to the spectra files
FILES		truncated path list to match the data being looked at
DATA		data from the spectra files
BADFILE		holds filename that has problems
BADCOMMENT	holds the comment associated with the bad file

START		index started at
END		index ended at

"""

#Select which data you want to check, will loop until a correct data source is selected
while (True):
	source = str(raw_input("Please select which data to check(type one of the following):\nbsnip\ncfa\ncsp\nother\nuv\n:"))
	if(source != 'bsnip' and source !='cfa' and source !='csp' and source !='other' and source !='uv'):
		print "\ninvalid data selection\n"
	else:
		print "checking",source
		break

#accounts for different file organizations for sources
if source == 'bsnip' or source == 'uv':
	path = "../data/spectra/"+source+"/*.flm"
if source == 'cfa':
	path = "../data/spectra/"+source+"/*/*.flm"
if source == 'csp' or source == 'other':
	path = "../data/spectra/"+source+"/*.dat"


#read in all filenames to extract data from 
filenames = glob.glob(path)

###checks that all the files were correctly read in
##for files in filenames:
##	print files

#select an index value to start at so you don't have to check a set of data
#from the beginning every time you run the program
while (True):
	print "valid index range: 0 to",(len(filenames)-1)
	try:
		start = int(raw_input("Please select what index you would like to start at?(-1 for list)\n:"))
		if start == -1:
			step = int(raw_input("Please enter step size(how many spectra per [enter])\n:"))
			print "PRESS [ENTER] TO SHOW NEXT",step,"(q to quit)"
			for j in range(len(filenames)):
				if source == 'cfa':
					print j,filenames[j].split('/')[5]
				else:
					print j,filenames[j].split('/')[4]
				if (j % step == 0):
					flag = raw_input();
					if flag == 'q':
						break
		if (start < 0 or start > (len(filenames)-1)):
			print "INDEX OUT OF RANGE\n"
		else:
			print "starting at index:",start		
			break
	except ValueError:
		print "NOT AN INTEGER\n"


data = []
wave = []
flux = []
badfile = []
badcomment = []
interp = []
invar = []
end = -1

"""
[ ] - need to implement
[x] - implemented
[!] - implemented but needs work
MAIN LOOP CHECKLIST:

	For each spectra file:

	[x]read data at index (from START)
	[x]except value error for bad file
	[x]make sure FILE lines up with DATA
	[x]create separate interpolated data INTERP
	[x]get inverse varience values INVAR
	[!]plot ORIG and INTERP data 
	 with INVAR
	[x]Observe and Comment(for BADFILE and BADCOMMENT):
		[x][enter](blank input)
		 	plot is fine(don't add to list)
		[x]type comment(telluric, spikes, clipping, etc...)
		 	add FILES[i] to BADFILE and 
			keyboard input to BADCOMMENT
		[x]'q' to end, saves ending index to END
	[x]Continues onto next file if not quitting

	if quitting:
		[]combine BADFILE and BADCOMMENT into 2-column list
		[]save list to txt file in format: 
		('SOURCE_'+'START'+'_'+'END')
		ex. ('cfa_0_200.txt')

"""
files = []
#############
##MAIN LOOP## see MAIN LOOP CHECKLIST above for breakdown
#############
offset = start
for i in range(len(filenames)):
    if (i >= start):
            try:
			###checks that correct data files are appended 
			###when taking into account the index offset
			##print i,filenames[i]

			#gets wave and flux from current file
                data.append((np.loadtxt(filenames[i])))
			#keeps track of files looking at (due to index offset)
                files.append(filenames[i])
		
		
			#separate wave/flux/error for easier manipulation
                orig_wave = data[i-offset][:,0]
                orig_flux = data[i-offset][:,1]
                try:
				# check if data has error array
                    orig_error = data[i-offset][:,2] 
                except IndexError:
				# if not, set default
                    orig_error = np.array([0])

			##get invar, to use in interp, and separate wave/flux/errors
                invar = genivar(orig_wave,orig_flux)
#                  print invar                           
                interp = Interpo(orig_wave,orig_flux,invar)
                interp_wave = interp[0]
                interp_flux = interp[1]
                interp_error = interp[2]
#                print interp_wave,interp_flux,interp_error

		##plotting orig, interp, var


                Relative_Flux = [orig_wave, orig_flux, interp_wave, interp_flux]  # Want to plot a composite of multiple spectrum
                Variance = invar
                Residuals     = []
                Spectra_Bin   = []
                Age           = []
                Delta         = []
                Redshift      = [] 
                Show_Data     = [Relative_Flux,Variance,Residuals,Spectra_Bin,Age,Delta,Redshift]
                image_title   = source,i            # Name the image (with location)
                title         = "checking",filenames[i]
		#
		## Available Plots:  Relative Flux, Residuals, Spectra/Bin, Age, Delta, Redshift, Multiple Spectrum, Stacked Spectrum
		##                   0              1          2            3    4      5         6,                 7
		####################################^should be varience?...
                name_array = ["original", " ", "interpolated", " "]
                Names = name_array
                Plots = [0,1] # the plots you want to create
		#
		## The following line will plot the data
		#
                xmin         = orig_wave[0]-50 
                xmax         = orig_wave[len(orig_wave)-1]+50
                # Use the plotting function here
                #Plotting.main(Show_Data , Plots , image_title , title, Names,xmin,xmax)
                print "FILE:",filenames[i]
                #test plotting (when Plotting code is not working properly)
                #plt.figure(1)
                plt.subplot(2,1,1)                
                plt.plot(orig_wave,orig_flux,'b',label = 'Original')
                plt.plot(interp_wave, interp_flux,'r',label = 'Interpolated')
                plt.xlim(xmin,xmax)
                plt.xlabel('Rest Wavelength')
                plt.ylabel('Flux')

                plt.subplot(2,1,2)
                plt.plot(orig_wave,invar)
                plt.xlim(xmin,xmax)
                plt.xlabel('Rest Wavelength')
                plt.ylabel('Inverse Variance')
                plt.show()
                #print "spectra is plotted"

                comment = str(raw_input("Please comment on this spectra\n([enter](blank) = no error, 'q' or 'quit' to stop)\n:"))
			#no error, don't record anything
                if comment == '':
			print "nothing to see here"
			print "move along, move along"
			#done checking, record ending index and stop loop
                elif comment == 'q' or comment == 'quit':
			end = i
			break
			#comment made, record it and the file to respective lists
                else:
			if source == 'cfa':
				badfile.append(filenames[j].split('/')[5])
			else:
				badfile.append(filenames[j].split('/')[4])

			badcomment.append(comment)
			print "COMMENT:",comment
				
				
            except ValueError:
			print "found bad file! at index:",i
			if source == 'cfa':
				badfile.append(filenames[j].split('/')[5])
			else:
				badfile.append(filenames[j].split('/')[4])
			badcomment.append("bad file")
			#can't read file ->messes up indexing and this corrects for this
			offset += 1

if end == -1:
	end = len(filenames)-1
###checks to make sure the right data is being looked at
##print "looking at",files[0],"with wave vals:\n",data[0][:,0]	#all wavelengths of data at index 0
##print "looking at",files[0],"with flux vals:\n",data[0][:,1]	#all flux values of data at index 0

###double-check to make sure right number of data are appended
##print len(filenames),"- starting index",start,"=",len(data)
##print badfile,badcomment

############
##QUITTING##
############
badlist =  Table([badfile,badcomment])
badlist_filename = "checked"+"_"+source+"_"+str(start)+"-"+str(end)
print "REVIEW:"
print "BADLIST FILENAME:",badlist_filename
print "LIST:\n",badlist
while(True):
	save = str(raw_input("save?(y/n)\n:"))
	if save == 'y':
		print "saving..."
		ascii.write(badlist,badlist_filename)
	elif save == 'n':
		safety = str(raw_input("are you sure you want to quit?(y/n)\n:"))
		if safety == 'y':
			print "quitting without saving..."
			break
		elif safety =='n':
			continue

	else:
		print "not valid input"

