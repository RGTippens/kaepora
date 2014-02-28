import os
import glob
from specutils import extinction as ex
from astropy.table import Table
from astropy.io import ascii
import astroquery
from astroquery.irsa_dust import IrsaDust
import numpy as np
import matplotlib.pyplot as plt
import scipy.interpolate as inter


#list of files
spectra_files = glob.glob ('../../data/cfa/*/*.flm')

#holds spectra data (wavelength,flux,weight)
spectra_data = []
#holds file pathname
file_path = []

junk_data = []

#number of spectra to modify
num = 100

#get data, pathnames
for i in range(num):
	try:
        	spectra_data.append(np.loadtxt(spectra_files[i]))
        	file_path.append(spectra_files[i][14:-4])
		#print file_path
             
	except ValueError:
		junk_data.append(spectra_files)

#update num to number of good spectra files
num = len(spectra_data)

#table containing sn names, redshifts, etc.
sn_parameters = np.genfromtxt('../../data/cfa/cfasnIa_param.dat',dtype = None)
#table containing B and V values for determining extinction -> dereddening due to milky way
sne= np.genfromtxt('extinction.dat', dtype = None)




#holds sn name
sn = []
#holds redshift value
z = []

#get relevent parameters needed for calculations
for i in range(len(sn_parameters)):
	sn.append(sn_parameters[i][0])
	z.append(sn_parameters[i][1])


"""
NOTE:
Using IRSA
"""

"""
Note: using parameters.dat file which was created from paramaters.py
parameters.py is designed to pull all relevant parameters for SNe spectra from online databases
via astroquery and place it all in a table to be pulled from later;
it would ideally do that following:
-read in all files we want to prep
-truncate file name to format "SNyear"(this is how astroquery searches for SN)
-get relevent data into table, following a format like:
SN name		Host Galaxy		Redshift	B	V	De-redden factor	CarbonPos/Neg

####
NOTE:Currently only has SN_name, B, and V values for purposes of Dereddening due to Milky way dust
####
"""

#deredden spectra due to milky way
#deredshift the spectra
for i in range(num):#go through selected spectra data
	for j in range(len(sn)):#go through list of SN parameters
		if sn[j] in file_path[i]:#SN with parameter matches the path
			print "\n###############################\nlooking at",sne[j+1],"matched with",sn[j]
			b = sne[j+1][1].astype(float)
			v = sne[j+1][2].astype(float)
			bv = b-v
			print "B-V=",bv
			print "starting flux:\n",spectra_data[i][:,1]
			#or use fm07 model
			spectra_data[i][:,1] = spectra_data[i][:,1]*ex.reddening(spectra_data[i][:,0],ebv=bv,r_v=3.1,model='f99')
			print "de-reddened with specutils f99 model:\n",spectra_data[i][:,1]
			print "starting wavelength:\n",spectra_data[i][:,0]
			spectra_data[i][:,0] /= (1+z[j])
			print "z:",z[j]
			print "de-red-shifted wavelength:\n",spectra_data[i][:,0]
print "\n##########\n##########\ndone de-reddening and de-redshifting"



