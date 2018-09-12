import os
import glob
from specutils import extinction as ex
from specutils import Spectrum1D
from astropy import units as u
import test_dered
#import astroquery
#from astroquery.ned import Ned
#from astroquery.irsa_dust import IrsaDust
from astropy.table import Table
from astropy.io import ascii
import numpy as np
import matplotlib.pyplot as plt
import scipy.interpolate as inter
import math
#import sqlite3 as sq3
#import msgpack

"""
README:

This part of code is written for composite spectra preparation.
It does deredding, deredshifting, and interpolation.
Using the function compprep:
INPUT :
SPECTRUM : table containing the original wavelength and flux
FILE_NAME : containing name of supernova
Z: redshift of the spectra
SOURCE : the dataset to analyze. Currently we have 'cfa''csp''bsnip'

OUTPUT:
NEW_DATA: table containing the processed wavelength, flux and variance

"""


def ReadParam():
    #Read in : table containing sn names, redshifts, etc.
    sn_param = np.genfromtxt('../data/cfa/cfasnIa_param.dat', dtype=None)
    sn = []
    z = []
    for i in range(len(sn_param)):
        sn.append(sn_param[i][0])  # get relevent parameters needed for calculations
        z.append(sn_param[i][1])  # redshift value
    return z


def ReadExtin(file):
    #table containing B and V values for determining extinction -> dereddening due to milky way
    sne = np.genfromtxt(file, dtype=None)

    return sne


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

#deredden spectra to milky way
#deredshift the spectra
#deredden to host galaxy


def dered(sne, snname, wave, flux):
    for j in range(len(sne)):  # go through list of SN parameters
        sn = sne[j][0]
        if sn in snname:  # SN with parameter matches the path
            b = sne[j][1].astype(float)
            v = sne[j][2].astype(float)
            bv = b-v
#            print "B(%s)-V(%s)=%s"%(b,v,bv)
#            print "R(v) =",r
            #or use fm07 model
            #test1 = spectra_data[i][:,1] * ex.reddening(spectra_data[i][:,0],ebv = bv, model='ccm89')
            #test2 = spectra_data[i][:,1] * ex.reddening(spectra_data[i][:,0],ebv = bv, model='od94')
            flux *= ex.reddening(wave, ebv=bv, r_v=3.1, model='f99')
#            wave /= (1+z)

            #print "de-reddened by host galaxy\n",flux*ex.reddening(wave,ebv = 0, r_v = r, model='f99')
            #host *= ex.reddening(wave,ebv = bv, r_v = r, model='f99')

    return flux

def host_correction(sne, snname, wave, flux):
    for j in range(len(sne)):  # go through list of SN parameters
        sn = sne[j][0]
        if sn in snname:  # SN with parameter matches the path
            a_v = sne[j][2].astype(float)
            flux *= ex.reddening(wave, ebv=3.1*a_v, r_v=3.1, model='f99')
    return flux


# Data Interpolation

"""
NOTE:
This function inputs three lists containing wavelength, flux and variance.
The output will be a Table with all the fitted values.
You can change the mininum and maximum of wavelength to output,
as well as pixel size in the first few lines.
For the spectra that does not cover the whole range of specified wavelength,
we output the outside values as NAN
"""

import datafidelity as df  # Get inverse variance from the datafidelity outcome

def Interpo (wave, flux, ivar):
    wave_min = 1000
    wave_max = 12000
    dw = 2

    #wavelength = np.linspace(wave_min,wave_max,(wave_max-wave_min)/pix+1)
    wavelength = np.arange(math.ceil(wave_min), math.floor(wave_max),
                           dtype=int, step=dw)  # creates N equally spaced wavelength values
    inter_flux = []
    inter_ivar = []
    output = []

    lower = wave[0]  # Find the area where interpolation is valid
    upper = wave[-1]

    #ivar = clip(wave, flux, ivar) #clip bad points in flux (if before interpolation)
    # ivar = clipmore(wave,flux,ivar)
#    print 'ivar', ivar
#    print 'bad points', bad_points
    #ivar[ivar < 0] = 0 # make sure no negative points

    good_data = np.where((wave >= lower) & (wave <= upper))  #creates an array of wavelength values between minimum and maximum wavelengths from new spectrum

    influx = inter.splrep(wave[good_data], flux[good_data])  # creates b-spline from new spectrum

    inivar = inter.splrep(wave[good_data], ivar[good_data])  # doing the same with the inverse varinces

    # extrapolating returns edge values
    inter_flux = inter.splev(wavelength, influx, ext = 3)	 # fits b-spline over wavelength range
    inter_ivar = inter.splev(wavelength, inivar, ext = 3)   # doing the same with errors

#    inter_ivar = clip(wavelength, inter_flux, inter_var) #clip bad points (if do after interpolation

    inter_ivar[inter_ivar < 0] = 0  # make sure there are no negative points!
    
#    place = np.where((wavelength > 5800.0 ) & (wavelength < 6000.0 ))
#    print inter_ivar[place]
    missing_data = np.where((wavelength < lower) | (wavelength > upper))
    inter_flux[missing_data] = float('NaN')  # set the bad values to NaN !!!
    inter_ivar[missing_data] = float('NaN')

#    print inter_ivar[place]

    output = np.array([wavelength, inter_flux, inter_ivar])  # put the interpolated data into the new table

    return output  # return new table


    # Get the Noise for each spectra ( with input of inverse variance)

def getsnr(flux, ivar):
    sqvar = map(math.sqrt, ivar)
    snr = flux/(np.divide(1.0, sqvar))
    snr_med = np.median(snr)
    return snr_med


def compprep(spectrum, sn_name, z, source, use_old_error=True, testing=False):
    old_wave = spectrum[:, 0]	    # wavelengths
    old_flux = spectrum[:, 1] 	# fluxes
    try:
        old_error = spectrum[:, 2]  # check if supernovae has error array
    except IndexError:
        old_error = None  # if not, set default
    if sn_name == '2011fe' and source == 'other':
        old_error = np.sqrt(old_error)
    if old_error is not None:
        old_var = old_error**2.
    else:
        old_var = None

    if old_var is not None:
        num_non_zeros = np.count_nonzero(old_var)
        if len(old_var) - num_non_zeros > 100:
            old_var = None
        elif old_var[-1] == 0.:
            old_var[-1] = old_var[-2]
        elif True in np.isnan(old_var):
            nan_inds = np.transpose(np.argwhere(np.isnan(old_var)))[0]
            for ind in nan_inds:
                if ind != 0:
                    old_var[ind] = old_var[ind-1]
                else:
                    old_var[ind] = old_var[ind+1]

    if testing:
        plt.plot(old_wave, old_flux)
        plt.show()
        if old_var is not None:
            plt.plot(old_wave, old_var)
            plt.show()
    # old_var = None
    vexp, SNR = df.find_vexp(old_wave, old_flux, var_y=old_var)
    if testing:
        print vexp, SNR
    old_wave, old_flux, old_var = df.clip(old_wave, old_flux, old_var, vexp, testing=testing) #clip emission/absorption lines
    temp_ivar, SNR = df.genivar(old_wave, old_flux, old_var, vexp=vexp, testing=testing)  # generate inverse variance
    if testing:
        print SNR

    if old_var is not None:
        old_ivar = 1./old_var
    else:
        old_ivar = temp_ivar
    # snr = getsnr(old_flux, old_ivar)

    if source == 'cfa':  # choosing source dataset
#        z = ReadParam()
        sne = ReadExtin('extinction.dat')
    if source == 'bsnip':
        sne = ReadExtin('extinctionbsnip.dat')
    if source == 'csp':
        sne = ReadExtin('extinctioncsp.dat')
        old_wave *= 1+float(z)  # Redshift back
    if source == 'uv':
        sne = ReadExtin('extinctionuv.dat')
    if source == 'other':
        sne = ReadExtin('extinctionother.dat')
    if source == 'swift_uv':
        sne = ReadExtin('extinctionswiftuv.dat')
    if source == 'foley_hst':
        sne = ReadExtin('extinctionhst.dat')

#     host_reddened = ReadExtin('../data/info_files/ryan_av.txt')
    newdata = []
    old_wave = old_wave*u.Angstrom        # wavelengths
    old_flux = old_flux*u.Unit('W m-2 angstrom-1 sr-1')
    spec1d = Spectrum1D.from_array(old_wave, old_flux)
    spec1d_ivar = Spectrum1D.from_array(old_wave, old_ivar)
    dered_flux, dered_ivar = test_dered.dered(sne, sn_name, spec1d.wavelength, spec1d.flux, spec1d_ivar.flux)  # Dereddening (see if sne in extinction files match the SN name)
#     new_flux = host_correction(sne, sn_name, old_wave, new_flux)

    # new_flux = old_flux
    new_flux = dered_flux.value
    new_ivar = dered_ivar.value
    old_wave = old_wave.value

    if testing:
        plt.plot(old_wave, old_flux)
        plt.plot(old_wave, new_flux)
        plt.show()
        plt.plot(old_wave, old_ivar)
        plt.plot(old_wave, new_ivar)
        plt.show()

    new_wave = old_wave/(1.+z)  # Deredshifting
    if not use_old_error:
        new_var = None
    else:
        new_var = old_var  # Placeholder if it needs to be changed
    #var = new_flux*0+1
    newdata = Interpo(new_wave, new_flux, new_ivar)  # Do the interpolation
    return newdata, SNR
