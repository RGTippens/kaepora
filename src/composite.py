"""
Spectra composite program
Authors: Sam, Yixian, Aaron
"""
#example: python Run.py 2 "SELECT * FROM Supernovae WHERE Carbon = 'A' AND Phase Between -6 and -4 AND Dm15 Between 0 and 2"
#msgpack_python version 0.4.6
#msgpack_numpy version 0.3.5
import matplotlib.pyplot as plt
import numpy as np
import glob
import sqlite3 as sq3
from scipy import interpolate as intp
import math
from astropy.table import Table
import msgpack as msg
import msgpack_numpy as mn
from scipy.optimize import leastsq
from scipy.special import erf
import file_name
import time
from lmfit import minimize, Parameters
import scipy.optimize as opt
import copy
from collections import Counter

from specutils import extinction as ex
import test_dered
import prep
from astropy import units as u
from specutils import Spectrum1D
import magnitudes as mg
import questionable_spectra as qspec
import telluric_spectra as tspec
import query_db as qdb
import spectral_analysis as sa

np.set_printoptions(threshold=np.nan)
mn.patch()

#Sets up some lists for later
SN_Array = []
full_array = []
compare_spectrum = []


class supernova(object):
	"""Contains all spectral data provided by the associated file.
	   Attributes can be added
	"""
	def __init__(self, wavelength = None, flux = None, ivar = None):#, spectra):
		if wavelength is not None:
			self.wavelength = wavelength
			self.flux = flux
			if ivar is None:
				self.ivar = np.zeros(len(flux))
			else:
				self.ivar = ivar
			self.low_conf = []
			self.up_conf = []
			self.x1 = 0
			self.x2 = len(wavelength) - 1
#Connect to database
#Make sure your file is in this location

#con = sq3.connect('../data/SNe.db')
# con = sq3.connect('../data/SNe_2.db')
# con = sq3.connect('../data/SNe_3.db')

def store_phot_data(SN, row):

	phot_row = row[19:]
	# SN.name      = phot_row[0]
	SN.ra        = phot_row[1]
	SN.dec       = phot_row[2]
	SN.zCMB_salt, SN.e_zCMB_salt, SN.Bmag_salt, SN.e_Bmag_salt, SN.s_salt, SN.e_s_salt, SN.c_salt, SN.e_c_salt, SN.mu_salt, SN.e_mu_salt = phot_row[3:13]
	SN.zCMB_salt2, SN.e_zCMB_salt2, SN.Bmag_salt2, SN.e_Bmag_salt2, SN.x1_salt2, SN.e_x1_salt2, SN.c_salt2, SN.e_c_salt2, SN.mu_salt2, SN.e_mu_salt2 = phot_row[13:23]
	SN.zCMB_mlcs31, SN.e_zCMB_mlcs31, SN.mu_mlcs31, SN.e_mu_mlcs31, SN.delta_mlcs31, SN.e_delta_mlcs31, SN.av_mlcs31, SN.e_av_mlcs31 = phot_row[23:31]
	SN.zCMB_mlcs17, SN.e_zCMB_mlcs17, SN.mu_mlcs17, SN.e_mu_mlcs17, SN.delta_mlcs17, SN.e_delta_mlcs17, SN.av_mlcs17, SN.e_av_mlcs17 = phot_row[31:39]
	SN.glon_host, SN.glat_host, SN.cz_host, SN.czLG_host, SN.czCMB_host, SN.mtype_host, SN.xpos_host, SN.ypos_host, SN.t1_host, SN.filt_host, SN.Ebv_host = phot_row[39:50]
	SN.zCMB_lc, SN.zhel_lc, SN.mb_lc, SN.e_mb_lc, SN.c_lc, SN.e_c_lc, SN.x1_lc, SN.e_x1_lc, SN.logMst_lc, SN.e_logMst_lc, SN.tmax_lc, SN.e_tmax_lc, SN.cov_mb_s_lc, SN.cov_mb_c_lc, SN.cov_s_c_lc, SN.bias_lc = phot_row[50:66]
	SN.av_25 = phot_row[66]
	SN.dm15_source = phot_row[67]
	SN.dm15_from_fits = phot_row[68]
	SN.e_dm15 = phot_row[69]
	SN.sep = phot_row[70]
	SN.ned_host = phot_row[71]
	SN.v_at_max = phot_row[72]
	SN.e_v = phot_row[73]
	SN.light_curves = msg.unpackb(phot_row[-2])
	SN.csp_light_curves = msg.unpackb(phot_row[-1])

def grab(sql_input, multi_epoch = False, make_corr = True, selection = 'max_coverage', grab_all=False):
	"""Pulls in all columns from the database for the selected query. 
	   Replaces all NaN values with 0. Returns the array of supernova objects 
	   with the newly added attributes.
	"""
	print "Collecting data..."
	con = sq3.connect('../data/SNe_19_phot_9.db')
	# con = sq3.connect('../data/SNe_14.db')
	cur = con.cursor()

	SN_Array = []
	# multi_epoch = raw_input("Include multiple epochs? (y/n): ")
	# if multi_epoch == 'y':
	#     multi_epoch = True
	# else:
	#     multi_epoch = False
	# multi_epoch = True

	get_phot = False
	if "join" in sql_input:
		get_phot = True

	cur.execute(sql_input)
	if 'phase' in sql_input:
		split_query = sql_input.split()
		p_index = split_query.index('phase')
		p_low = float(split_query[p_index+2])
		p_high = float(split_query[p_index+6])
		p_avg = (p_low+p_high)/2.
	# print len(list(cur))
	# raise TypeError
	for row in cur:
		SN           = supernova()
		SN.filename  = row[0]
		SN.name      = row[1]
		SN.source    = row[2]
		SN.redshift  = row[3]
		SN.phase     = row[4]
		SN.minwave   = row[5]
		SN.maxwave   = row[6]
		SN.dm15      = row[7]
		SN.m_b       = row[8]
		SN.B_minus_V = row[9]
		SN.velocity  = row[10]
		SN.morph     = row[11]
		SN.carbon    = row[12]
		SN.GasRich   = row[13]
		SN.SNR       = row[14]
		SN.resid     = row[15]
		interp       = msg.unpackb(row[16])
		SN.interp    = interp
		SN.mjd         = row[17]
		SN.ref       = row[18]

		if get_phot:
			store_phot_data(SN, row)

		SN.low_conf  = []
		SN.up_conf   = []
		SN.spec_bin  = []

		try:
			SN.wavelength = SN.interp[0,:]
			SN.flux       = SN.interp[1,:]
			SN.ivar       = SN.interp[2,:]
		except TypeError:
			print "ERROR: ", SN.filename, SN.interp
			continue
		full_array.append(SN)
		SN_Array.append(SN)

	if grab_all:
		return SN_Array

		
		# for i in range(len(SN_Array-1)): 
		#     if SN_Array[i].name == SN_Array[i-1].name and not multi_epoch:
		#         if abs(SN_Array[i].phase) < abs(SN_Array[i-1].phase): # closest to maximum
		#         # if abs(SN_Array[i].SNR) > abs(SN_Array[i-1].SNR): # best signal to noise
		#             del SN_Array[i-1]

	if make_corr:
		bad_files = qspec.bad_files()

		bad_ivars = []
		for SN in SN_Array:
			# print SN.filename 
			if len(np.where(np.isnan(SN.ivar))[0] == True) == 5500:
				bad_ivars.append(SN.filename)
				# plt.plot(SN.wavelength,SN.flux)
				# plt.show()
		if len(bad_ivars) > 0:
			print "Generate variance failed for: ", bad_ivars

		len_before = len(SN_Array)
		good_SN_Array = [SN for SN in SN_Array if not is_bad_data(SN, bad_files, bad_ivars)]
		SN_Array = good_SN_Array
		print len_before - len(SN_Array), 'questionable spectra removed', len(SN_Array), 'spectra left'

		# remove peculiar Ias
		len_before = len(SN_Array)
		SN_Array = remove_peculiars(SN_Array,'../data/info_files/pec_Ias.txt')
		print len_before - len(SN_Array), 'Peculiar Ias removed', len(SN_Array), 'spectra left'

		SN_Array = check_host_corrections(SN_Array)

	if not multi_epoch:
		bad_files = qspec.bad_files()
		unique_events = []
		new_SN_Array = []
		for i in range(len(SN_Array)): 
			# print SN_Array[i].name, SN_Array[i].phase, SN_Array[i].source, SN_Array[i].filename, SN_Array[i].minwave, SN_Array[i].maxwave
			if SN_Array[i].name not in unique_events:
				unique_events.append(SN_Array[i].name)
		for i in range(len(unique_events)):
			events = []
			for SN in SN_Array:
				if SN.name == unique_events[i]:
					events.append(SN)
			# min_phase = events[0]
			# for e in events:
			#     if abs(e.phase) < abs(min_phase.phase):
			#         min_phase = e
			# new_SN_Array.append(min_phase)


			if selection == 'max_coverage':
				max_range = events[0]
				for e in events:
					if (e.maxwave - e.minwave) > (max_range.maxwave - max_range.minwave):
						max_range = e
				if not (events[0].name == '2011fe' and events[0].source == 'other'): #ignore high SNR 2011fe data
					new_SN_Array.append(max_range)
				# new_SN_Array.append(max_range)
			elif selection == 'max_coverage_choose_uv':
				max_range = events[0]
				for e in events:
					if e.source == 'swift_uv' or e.source == 'uv' and e.filename not in bad_files:
						max_range = e
					# elif (e.maxwave - e.minwave) > (max_range.maxwave - max_range.minwave):
					# 	max_range = e
					elif (e.minwave) < (max_range.minwave):
						max_range = e
				if not (events[0].name == '2011fe' and events[0].source == 'other'): #ignore high SNR 2011fe data
					new_SN_Array.append(max_range)
			elif selection == 'choose_bluest':
				bluest = events[0]
				for e in events:
					if e.minwave < bluest.minwave:
						bluest = e
				if not (events[0].name == '2011fe' and events[0].source == 'other'): #ignore high SNR 2011fe data
					new_SN_Array.append(bluest)
			elif selection == 'max_snr':
				max_snr = events[0]
				for e in events:
					if e.SNR != None and max_snr.SNR != None and abs(e.SNR) > abs(max_snr.SNR):
						max_snr = e
				if not (events[0].name == '2011fe' and events[0].source == 'other'): #ignore high SNR 2011fe data
					new_SN_Array.append(max_snr)
			elif selection == 'accurate_phase':
				#this should be smarter
				ac_phase = events[0]
				for e in events:
					if abs(e.phase - p_avg) < abs(ac_phase.phase - p_avg):
						ac_phase = e
				if not (events[0].name == '2011fe' and events[0].source == 'other'): #ignore high SNR 2011fe data
					new_SN_Array.append(ac_phase)
			elif selection == 'max_coverage_splice':
				max_range = events[0]
				for e in events:
					if (e.maxwave - e.minwave) > (max_range.maxwave - max_range.minwave):
						max_range = e
				splice_specs = []
				cur_min = max_range.minwave
				cur_max = max_range.maxwave
				for e in events:
					if (e.maxwave > cur_min and e.maxwave < cur_max):
						if (e.minwave < cur_min):
							olap = e.maxwave - cur_min
							cur_min = e.minwave
						else:
							olap = 0.
					elif (e.minwave < cur_max and e.minwave > cur_min):
						if (e.maxwave > cur_max):
							olap = cur_max - e.minwave
							cur_max = e.maxwave
						else:
							olap = 0.
					else:
						olap=0.
					if olap > 0. and olap < .5*(max_range.maxwave - max_range.minwave):
						if e is not max_range:
							splice_specs.append(e)
				if not (events[0].name == '2011fe' and events[0].source == 'other'): #ignore high SNR 2011fe data
					new_SN_Array.append(max_range)
				for spec in splice_specs:
					new_SN_Array.append(spec)

		SN_Array = new_SN_Array

	print len(SN_Array), "valid SNe found"

	# print "Creating event file..."
	# mg.generate_event_list(SN_Array)
	# print "Event file done."
	
	#make cuts

	for SN in SN_Array:
		SN.phase_array = np.array(SN.flux)
		SN.dm15_array  = np.array(SN.flux)
		SN.red_array   = np.array(SN.flux)
		SN.vel         = np.array(SN.flux)
		# print SN.name, SN.dm15, SN.dm15_cfa, SN.dm15_from_fits, SN.filename

		nan_bool_flux = np.isnan(SN.flux)
		non_nan_data = np.where(nan_bool_flux == False)
		nan_data = np.where(nan_bool_flux == True)
		SN.flux[nan_data]         = np.nan
		SN.ivar[nan_data] 		  = 0
		SN.phase_array[nan_data]  = np.nan
		SN.dm15_array[nan_data]   = np.nan
		SN.red_array[nan_data]    = np.nan
		SN.vel[nan_data]          = np.nan
		if SN.phase != None:
			SN.phase_array[non_nan_data] = SN.phase
		else:
			SN.phase_array[non_nan_data] = np.nan
		if get_phot:
			if SN.dm15_source != None:
				SN.dm15_array[non_nan_data] = SN.dm15_source
			elif SN.dm15_from_fits != None:
				SN.dm15_array[non_nan_data] = SN.dm15_from_fits
			else:
				SN.dm15_array[non_nan_data] = np.nan
		if SN.redshift != None:
			SN.red_array[non_nan_data] = SN.redshift
		else:
			SN.red_array[non_nan_data] = np.nan
		if SN.velocity != None:
			SN.vel[non_nan_data] = SN.velocity
		else:
			SN.vel[non_nan_data] = np.nan

		non_nan_data = np.array(non_nan_data[0])
		if len(non_nan_data) > 0:
			SN.x1 = non_nan_data[0]
			SN.x2 = non_nan_data[-1]
			SN.x2 += 1
		else:
			SN.x1 = 0
			SN.x2 = 0

		# SN.ivar[SN.x1:SN.x1 + 25] = 0.
		# SN.ivar[SN.x2 - 25:SN.x2 + 1] = 0.
		SN.x1 = SN.x1 + 25
		SN.x2 = SN.x2 - 25

					
	print "Arrays cleaned"
	return SN_Array

	
def spectra_per_bin(SN_Array):
	"""Counts the number of spectra contributing to the composite at any given 
	   wavelength. Returns array to be plotted over the wavelength range.
	"""
	spec_per_bin = []
	
	for i in range(len(SN_Array[0].flux)):
		count = 0
		for SN in SN_Array:
			if SN.flux[i] != 0 and SN.ivar[i] != 0:   
				count += 1
		spec_per_bin.append(count)
	
	return spec_per_bin
			
			
def optimize_scales(SN_Array, template, initial):
	"""Scales each unique supernova in SN_Array by minimizing the square residuals
	   between the supernova flux and the template flux. This also works for bootstrap
	   arrays (can contain repeated spectra) because the objects in SN_Array are not 
	   copies. Returns scaled SN_Array and the scales that were used.
	"""
	scales = []
	unique_arr = list(set(SN_Array))
	guess = 1.0
	for uSN in unique_arr:
		# guess = 1.0
		guess = np.average(template.flux[template.x1:template.x2])/np.average(uSN.flux[uSN.x1:uSN.x2])
		# guess = template.flux[2000]/uSN.flux[2000] #this is temporary it does not work for every spectrum 
		# if uSN.filename != template.filename:
		# 	u = opt.minimize(sq_residuals, guess, args = (uSN, template, initial), 
		# 					 method = 'Nelder-Mead').x
		# 	scales.append(u)
		# else:
		# 	scales.append(1.0)
		u = opt.minimize(sq_residuals, guess, args = (uSN, template, initial), 
						 method = 'Nelder-Mead').x
		scales.append(u)
		
	for i in range(len(unique_arr)):
		unique_arr[i].flux = scales[i]*unique_arr[i].flux
		unique_arr[i].ivar /= (scales[i])**2
		if len(unique_arr[i].low_conf) > 0 and len(unique_arr[i].up_conf) > 0:
			unique_arr[i].low_conf = scales[i]*unique_arr[i].low_conf
			unique_arr[i].up_conf = scales[i]*unique_arr[i].up_conf


		
	return SN_Array, scales
	
	
def sq_residuals(s,SN,comp, initial):
	"""Calculates the sum of the square residuals between two supernova flux 
	   arrays usinig a given scale s. Returns the sum.
	"""
#    print s
	s = np.absolute(s)
	if SN.x1 <= comp.x1 and SN.x2 >= comp.x2:
		pos1 = comp.x1
		pos2 = comp.x2
	elif SN.x1 >= comp.x1 and SN.x2 <= comp.x2:
		pos1 = SN.x1
		pos2 = SN.x2
	elif SN.x1 >= comp.x1 and SN.x1 <= comp.x2 and SN.x2 >= comp.x2:
		pos1 = SN.x1
		pos2 = comp.x2
	elif SN.x1 <= comp.x1 and SN.x2 >= comp.x1 and SN.x2 <= comp.x2:
		pos1 = comp.x1
		pos2 = SN.x2
	else: 
		#residual of first index will always be zero (won't be scaled)
		# print "no overlap"
		pos1 = 0
		pos2 = 0
	temp_flux = s*SN.flux
	res = temp_flux[pos1:pos2] - comp.flux[pos1:pos2]
	sq_res = res*res
	if initial:
		return np.sum(sq_res)
	else:
		temp_ivar = SN.ivar/(s*s)
		w_res = temp_ivar[pos1:pos2]*sq_res
		return np.sum(w_res)
	
def mask(SN_Array, boot):
	"""Creates data structures to contain relevant data for the task needed 
	   (creating the composite or bootstrapping). Applies masks the these data 
	   for consistency and zero compensation. Returns the masks and data structures.
	"""
	#create 2D arrays of all available data
	fluxes = []
	ivars  = []
	reds   = []
	phases = []
	ages   = []
	vels   = []
	dm15s  = []
	dm15_ivars = []
	red_ivars  = []
	dm15_mask  = []
	red_mask   = []
	# for SN in SN_Array:
	#     if len(fluxes) == 0:
	#         fluxes = np.array([SN.flux])
	#         ivars  = np.array([SN.ivar])
	#         if not boot:
	#             reds   = np.array([SN.red_array])
	#             phases = np.array([SN.phase])
	#             ages   = np.array([SN.phase_array])
	#             vels   = np.array([SN.vel])
	#             dm15s  = np.array([SN.dm15_array])
	#     else:
	#         try:
	#             fluxes = np.append(fluxes, np.array([SN.flux]), axis=0)
	#             ivars  = np.append(ivars, np.array([SN.ivar]), axis=0)
	#             if not boot:
	#                 reds   = np.append(reds, np.array([SN.red_array]), axis = 0)
	#                 phases = np.append(phases, np.array([SN.phase]), axis = 0)
	#                 ages   = np.append(ages, np.array([SN.phase_array]), axis = 0)
	#                 vels   = np.append(vels, np.array([SN.vel]), axis = 0)
	#                 dm15s  = np.append(dm15s, np.array([SN.dm15_array]), axis = 0)
	#         except ValueError:
	#             print "This should never happen!"
	for SN in SN_Array:
		fluxes.append(SN.flux)
		ivars.append(SN.ivar)
		if not boot:
			reds.append(SN.red_array)
			phases.append(SN.phase)
			ages.append(SN.phase_array)
			vels.append(SN.vel)
			dm15s.append(SN.dm15_array)
	
	fluxes = np.ma.masked_array(fluxes,np.isnan(fluxes))
	reds   = np.ma.masked_array(reds,np.isnan(reds))
	phases = np.ma.masked_array(phases,np.isnan(phases))
	ages   = np.ma.masked_array(ages,np.isnan(ages))
	vels   = np.ma.masked_array(vels,np.isnan(vels))
	dm15s  = np.ma.masked_array(dm15s,np.isnan(dm15s))
	dm15_ivars = np.ma.masked_array(dm15_ivars,np.isnan(dm15_ivars))
	red_ivars  = np.ma.masked_array(red_ivars,np.isnan(red_ivars))
	dm15_mask  = np.ma.masked_array(dm15_mask,np.isnan(dm15_mask))
	red_mask   = np.ma.masked_array(red_mask,np.isnan(red_mask))
	flux_mask = []
	ivar_mask = []
	#Adding masks for every parameter 
	# flux_mask = np.zeros(len(fluxes[0,:]))
	# ivar_mask = np.zeros(len(fluxes[0,:]))
	# if not boot:
	#     dm15_mask = np.zeros(len(dm15s[0,:]))
	#     red_mask  = np.zeros(len(reds[0,:]))
	
	# have_data = np.where(np.sum(ivars, axis = 0)>0)
	# no_data   = np.where(np.sum(ivars, axis = 0)==0)
	# if not boot:
	#     no_dm15   = np.where(np.sum(dm15s, axis = 0)==0)
	#     no_reds   = np.where(np.sum(reds, axis = 0)==0)
	#     dm15_mask[no_dm15] = 0
	
	# ivar_mask[no_data] = 10e6
	
	# #Right now all of our spectra have redshift data, so a mask is unnecessary
	# #One day that might change
	# if not boot:
	#     red_mask[:]  = 0
		
	#     dm15_ivars = np.array(ivars)
	#     red_ivars  = np.array(ivars)
	
	# #Add in flux/ivar mask
	# fluxes = np.append(fluxes, np.array([flux_mask]), axis=0)
	# ivars  = np.append(ivars, np.array([ivar_mask]), axis=0)
	# if not boot:
	#     reds   = np.append(reds, np.array([flux_mask]), axis=0)
	#     ages   = np.append(ages, np.array([flux_mask]), axis=0)
	#     vels   = np.append(vels, np.array([flux_mask]), axis=0)
	#     dm15s  = np.append(dm15s, np.array([dm15_mask]), axis=0)
	#     dm15_ivars = np.append(dm15_ivars, np.array([dm15_mask]), axis=0)
	#     red_ivars  = np.append(red_ivars, np.array([red_mask]), axis=0)
		
	#     for i in range(len(dm15_ivars)):
	#         for j in range(len(dm15_ivars[i])):
	#             if dm15_ivars[i,j] == 0.0:
	#                 dm15_ivars[i,j] = 0.0
	
	return (fluxes, ivars, dm15_ivars, red_ivars, reds, phases, ages, vels, 
			dm15s, flux_mask, ivar_mask, dm15_mask, red_mask)
				

def average(SN_Array, template, medmean, boot, fluxes, ivars, dm15_ivars, red_ivars, 
				reds, phases, ages, vels, dm15s, flux_mask, ivar_mask, dm15_mask, red_mask):
	"""Modifies the template supernova to be the inverse variance weighted average
	   of the scaled data. Returns the new template supernova. 
	"""
	temp_fluxes = []
	# for i in range(len(SN_Array)):
	#     fluxes[i] = SN_Array[i].flux
	#     ivars[i] = SN_Array[i].ivar
	#     if medmean == 2:
	#         fluxes[i][fluxes[i] == 0] = np.nan
	#         if not boot:
	#             ages[i][ages[i] == 0] = np.nan
	#             vels[i][vels[i] == 0] = np.nan
	#             dm15s[i][dm15s[i] == 0] = np.nan
	#             reds[i][reds[i] == 0] = np.nan

		# temp_fluxes.append(np.ma.masked_where(fluxes[i] == 0, fluxes[i]))    
		# temp_fluxes.append(fluxes[i][fluxes[i] == 0] = np.nan) 
	
	# print temp_fluxes

	# if medmean == 1: 
	#     template.flux  = np.average(fluxes, weights=ivars, axis=0)
	#     if not boot:
	#         template.phase_array   = np.average(ages, weights=ivars, axis=0)
	#         template.vel   = np.average(vels, weights=ivars, axis=0)
	#         template.dm15  = np.average(dm15s, weights=dm15_ivars, axis=0)
	#         template.red_array = np.average(np.array(reds), weights = red_ivars, axis=0)
	# raise TypeError
	if medmean == 1: 
		template.flux  = np.ma.average(fluxes, weights=ivars, axis=0).filled(np.nan)
		# template.flux  = np.ma.average(fluxes, axis=0).filled(np.nan)
		if not boot:
			template.phase_array   = np.ma.average(ages, weights=ivars, axis=0).filled(np.nan)
			template.vel   = np.ma.average(vels, weights=ivars, axis=0).filled(np.nan)
			template.dm15_array  = np.ma.average(dm15s, weights=ivars, axis=0).filled(np.nan)
			template.red_array = np.ma.average(reds, weights = ivars, axis=0).filled(np.nan)
	if medmean == 2:
		# template.flux  = np.median(fluxes, axis=0)
		# template.flux  = np.ma.median(temp_fluxes, axis=0).filled(0)
		template.flux = np.nanmedian(fluxes, axis=0)
		if not boot:
			template.phase_array   = np.nanmedian(ages, axis=0)
			template.vel   = np.nanmedian(vels, axis=0)
			template.dm15_array  = np.nanmedian(dm15s, axis=0)
			template.red_array = np.nanmedian(reds, axis=0)
	
	#finds and stores the variance data of the template
	no_data   = np.where(np.sum(ivars, axis = 0)==0)
	template.ivar = np.sum(ivars, axis=0)
	template.ivar[no_data] = 0
	template.name = "Composite Spectrum"
	return template

		
def bootstrapping (SN_Array, samples, scales, og_template, iters, medmean):
	"""Creates a matrix of random sets of supernovae from the original sample 
	   with the same size as the original sample. The number of samples is 
	   defined by the user. Then creates and plots the composite spectrum for 
	   each of these sets. These data are used to contruct a confidence 
	   interval for the original sample. Returns flux arrays corresponding top 
	   the upper and lower intervals.
	"""
	strap_matrix = np.random.random_sample((samples, len(SN_Array)))
	strap_matrix *= len(SN_Array)
	strap_matrix = strap_matrix.astype(int)   
	boot_arr = []
	boots = []
	boot = True
	
	cpy_array = []
	for SN in SN_Array:
		cpy_array.append(copy.copy(SN))
		
	
	for i in range(len(strap_matrix)):
		boot_arr.append([])
		for j in range(len(strap_matrix[i])):
			boot_arr[i].append(cpy_array[strap_matrix[i,j]])
			

	for p in range(len(boot_arr)):
		# print p
		lengths = []
		for SN in boot_arr[p]:	
			lengths.append(len(SN.flux[np.where(SN.flux != 0)]))
		boot_temp = [SN for SN in boot_arr[p] if len(SN.flux[np.where(SN.flux!=0)]) == max(lengths)]
		boot_temp = copy.copy(boot_temp[0])
		
		(fluxes, ivars, dm15_ivars, red_ivars, reds, phases, ages, vels, dm15s, 
		 flux_mask, ivar_mask, dm15_mask, red_mask) = mask(boot_arr[p], boot)
		for x in range(iters):
			SN_Array, scales = optimize_scales(boot_arr[p], boot_temp, False)
			(fluxes, ivars, dm15_ivars, red_ivars, reds, phases, ages, vels, dm15s, 
			 flux_mask, ivar_mask, dm15_mask, red_mask) = mask(boot_arr[p], boot)
			template = average(boot_arr[p], boot_temp, medmean, boot, fluxes, ivars, dm15_ivars, red_ivars, 
							   reds, phases, ages, vels, dm15s, flux_mask, ivar_mask, dm15_mask, red_mask)
		boots.append(copy.copy(template))

	print "scaling boots..."
	temp1, scales = optimize_scales(boots, og_template, True)

	#examine bootstrap samples
	print "plotting..."
	# for SN in boots:
	#     plt.plot(SN.wavelength, SN.flux, 'g')
	# plt.plot(og_template.wavelength,og_template.flux, 'k', linewidth = 4)
	# plt.show()
	
	print "computing confidence intervals..."
	resid = []
	percentile = erf(1/np.sqrt(2.))
	low_pc = 0.5 - percentile*0.5
	up_pc = 0.5 + percentile*0.5

	for SN in boots:
#        temp = SN.flux - og_template.flux
		resid.append(SN.flux - og_template.flux)
#        non_olap = np.where(og_template.flux + temp == 0.0)
#        temp = np.delete(temp, non_olap)
#        resid.append(temp)
		
	resid_trans = np.transpose(resid)
	resid_sort = np.sort(resid_trans)
	arr = []
	new_resid = []
	for i in range(len(resid_sort)):
		# non_olap = []
		# for j in range (len(resid_sort[i])):
		# 	# if resid_sort[i][j] + og_template.flux[i] == 0.0 and og_template.flux[i] != 0.0:
		# 	if np.isnan(resid_sort[i][j] + og_template.flux[i]) and np.isnan(og_template.flux[i]) == False:
		# 		# print 'here'
		# 		non_olap.append(j)
		# new_resid.append(np.delete(resid_sort[i],non_olap))
		if True in np.isfinite(resid_sort[i]):
			new_resid.append(resid_sort[i][np.isfinite(resid_sort[i])])
		else:
			new_resid.append(resid_sort[i])

	# for elem in resid_sort:
	# 	for i in range (len(elem)):
	# 		if np.isfinite(elem[i]):
	# 			arr.append(elem[i])
	# plt.hist(arr,100)
	# plt.show()
	
	low_arr = []
	up_arr = []
	for i in range(len(new_resid)):
		low_ind = np.round((len(new_resid[i])-1) * low_pc).astype(int)
		up_ind = np.round((len(new_resid[i])-1) * up_pc).astype(int)
		low_arr.append(og_template.flux[i] + new_resid[i][low_ind])
		up_arr.append(og_template.flux[i] + new_resid[i][up_ind])
		
#    for i in range(len(resid_sort)):
#        print len(resid_sort[i])
#        low_ind = np.round((len(resid_sort[i])-1) * low_pc).astype(int)
#        up_ind = np.round((len(resid_sort[i])-1) * up_pc).astype(int)
#        low_arr.append(og_template.flux[i] + resid_sort[i][low_ind])
#        up_arr.append(og_template.flux[i] + resid_sort[i][up_ind])
	
	# plt.plot(og_template.wavelength, og_template.flux, 'k', linewidth = 4)
	# plt.fill_between(og_template.wavelength, low_arr, up_arr, color = 'green')
	# plt.show()
	
	# SN_Array = cpy_array
	return np.asarray(low_arr), np.asarray(up_arr), boots        
	
def is_bad_data(SN, bad_files, bad_ivars):
	bad_sns = ['2002bf']
	for el in bad_files:
		if SN.filename == el:
			return True
	for el in bad_ivars:
		if SN.filename == el:
			return True
	for el in bad_sns:
		if SN.name == el:
			return True
	return False

def remove_peculiars(SN_Array, file):
	SN_Array_no_pecs = []
	count = 1
	with open(file) as f:
		names = np.loadtxt(f, dtype = str)
		for SN in SN_Array:
			if SN.name not in names:
				SN_Array_no_pecs.append(SN)
			else:
				# print count, SN.name
				count += 1

	return SN_Array_no_pecs

def build_av_dict(file):
	 with open(file) as f:
		lines = f.readlines()

		av_dict = {}
		for line in lines:
			l = line.split()    
			if len(l) == 30 and l[0] == 'SN:':
				av_dict[l[1].lower()] = float(l[18])

	 return av_dict

def split_list(n):
	"""will return the list index"""
	return [(x+1) for x,y in zip(n, n[1:]) if y-x != 1.]

def get_sub_list(my_list):
	"""will split the list base on the index"""
	my_index = split_list(my_list)
	output = list()
	prev = 0
	for index in my_index:
		new_list = [ x for x in my_list[prev:] if x < index]
		output.append(new_list)
		prev += len(new_list)
	output.append([ x for x in my_list[prev:]])
	return output

def check_host_corrections(SN_Array):
	has_host_corr = []
	for SN in SN_Array:
		if SN.av_25 != None:
			has_host_corr.append(SN)
		elif SN.av_mlcs31 != None:
			has_host_corr.append(SN)
		elif SN.av_mlcs17 != None:
			has_host_corr.append(SN)
		# else:
		# 	print SN.name
	SN_Array = has_host_corr
	print len(SN_Array), 'spectra with host corrections'
	return SN_Array

def apply_host_corrections(SN_Array, lengths, r_v = 2.5, verbose=True):
	corrected_SNs = []
	for SN in SN_Array:
		if verbose:
			print SN.name, SN.filename, SN.SNR, SN.dm15_source, SN.dm15_from_fits, SN.phase, SN.redshift, SN.source, SN.wavelength[SN.x1], SN.wavelength[SN.x2], SN.ned_host
		# print SN.name, SN.av_25, SN.av_mlcs31, SN.av_mlcs17

		if SN.av_25 != None:
			# print "AV: ", SN.av_25
			pre_scale = (1.e-15/np.average(SN.flux[SN.x1:SN.x2]))
			SN.flux = pre_scale*SN.flux
			SN.ivar = SN.ivar/(pre_scale*pre_scale)
			old_wave = SN.wavelength*u.Angstrom        # wavelengths
			old_flux = SN.flux*u.Unit('W m-2 angstrom-1 sr-1')
			spec1d = Spectrum1D.from_array(old_wave, old_flux)
			old_ivar = SN.ivar*u.Unit('W m-2 angstrom-1 sr-1')
			# new_flux = test_dered.dered(sne, SN.name, spec1d.wavelength, spec1d.flux)
			new_flux, new_ivar = test_dered.host_correction(SN.av_25, r_v, SN.name, old_wave, old_flux, old_ivar)
			SN.flux = new_flux.value
			SN.ivar = new_ivar.value
			# lengths.append(len(SN.flux[np.where(SN.flux != 0)]))
			corrected_SNs.append(SN)
			lengths.append(len(SN.flux[np.where(SN.flux != 0)]))

		elif SN.av_mlcs31 != None:
			# print "AV: ", SN.av_mlcs31
			pre_scale = (1.e-15/np.average(SN.flux[SN.x1:SN.x2]))
			SN.flux = pre_scale*SN.flux
			SN.ivar = SN.ivar/(pre_scale*pre_scale)
			old_wave = SN.wavelength*u.Angstrom        # wavelengths
			old_flux = SN.flux*u.Unit('W m-2 angstrom-1 sr-1')
			spec1d = Spectrum1D.from_array(old_wave, old_flux)
			old_ivar = SN.ivar*u.Unit('W m-2 angstrom-1 sr-1')
			# new_flux = test_dered.dered(sne, SN.name, spec1d.wavelength, spec1d.flux)
			new_flux, new_ivar = test_dered.host_correction(SN.av_mlcs31, 3.1, SN.name, old_wave, old_flux, old_ivar)
			SN.flux = new_flux.value
			SN.ivar = new_ivar.value
			# lengths.append(len(SN.flux[np.where(SN.flux != 0)]))
			corrected_SNs.append(SN)
			lengths.append(len(SN.flux[np.where(SN.flux != 0)]))

		elif SN.av_mlcs17 != None:
			# print "AV: ", SN.av_mlcs17
			pre_scale = (1.e-15/np.average(SN.flux[SN.x1:SN.x2]))
			SN.flux = pre_scale*SN.flux
			SN.ivar = SN.ivar/(pre_scale*pre_scale)
			old_wave = SN.wavelength*u.Angstrom        # wavelengths
			old_flux = SN.flux*u.Unit('W m-2 angstrom-1 sr-1')
			spec1d = Spectrum1D.from_array(old_wave, old_flux)
			old_ivar = SN.ivar*u.Unit('W m-2 angstrom-1 sr-1')
			# new_flux = test_dered.dered(sne, SN.name, spec1d.wavelength, spec1d.flux)
			new_flux, new_ivar = test_dered.host_correction(SN.av_mlcs17, 1.7, SN.name, old_wave, old_flux, old_ivar)
			SN.flux = new_flux.value
			SN.ivar = new_ivar.value
			# lengths.append(len(SN.flux[np.where(SN.flux != 0)]))
			corrected_SNs.append(SN)
			lengths.append(len(SN.flux[np.where(SN.flux != 0)]))

	SN_Array = corrected_SNs
	print len(SN_Array), 'SNs with host corrections'
	return SN_Array


def remove_tell_files(SN_Array):
	tell_files = tspec.tel_spec()
	has_tell_file = False 
	for SN in SN_Array:
		if SN.filename in tell_files:
			has_tell_file = True 

	if has_tell_file:
		SN_Array_wo_tell = []
		for SN in SN_Array:
			if SN.filename not in tell_files:
				SN_Array_wo_tell.append(copy.copy(SN))
		return SN_Array_wo_tell
	else:
		return []

	

def create_composite(SN_Array, boot, template, medmean):
	i = 0
	scales  = []
	iters = 3
	iters_comp = 3
	# boot = False

	if boot is True:
		bootstrap = 'y'
	else:
		bootstrap = 'n'
	print "Creating composite..."
	optimize_scales(SN_Array, template, True)
	(fluxes, ivars, dm15_ivars, red_ivars, reds, phases, ages, vels, dm15s, 
	 flux_mask, ivar_mask, dm15_mask, red_mask) = mask(SN_Array, False)

	for i in range(iters_comp):
		SN_Array, scales = optimize_scales(SN_Array, template, False)
		(fluxes, ivars, dm15_ivars, red_ivars, reds, phases, ages, vels, dm15s, 
		 flux_mask, ivar_mask, dm15_mask, red_mask) = mask(SN_Array, False)
		template = average(SN_Array, template, medmean, False, fluxes, ivars, dm15_ivars, red_ivars, 
							reds, phases, ages, vels, dm15s, flux_mask, ivar_mask, dm15_mask, red_mask)
	print "Done."
	boots = None
	norm = 1./np.amax(template.flux[template.x1:template.x2])
	# norm = 1./np.amax(template.flux[np.where((template.wavelength > 3500.) & (template.wavelength < 8000.))])
	template.flux = template.flux*norm
	for SN in SN_Array:
		SN.flux = SN.flux*norm
		SN.ivar = SN.ivar/(norm**2.)
	#plot composite with the scaled spectra
	# plt.figure(num = 2, dpi = 100, figsize = [30, 20], facecolor = 'w')
	# for SN in SN_Array:
	# 	print np.average(SN.flux[SN.x1:SN.x2]), np.average(SN.ivar[SN.x1:SN.x2])

	if bootstrap is 'n':
		template.ivar = np.ones(len(template.wavelength))
		# plt.rc('font', family='serif')
		# fig, ax = plt.subplots(1,1)
		# fig.set_size_inches(10, 8, forward = True)
		# plt.minorticks_on()
		# plt.xticks(fontsize = 20)
		# ax.xaxis.set_ticks(np.arange(np.round(template.wavelength[template.x1:template.x2][0],-3), np.round(template.wavelength[template.x1:template.x2][-1],-3),1000))
		# plt.yticks(fontsize = 20)
		# plt.tick_params(
		#     which='major', 
		#     bottom='on', 
		#     top='on',
		#     left='on',
		#     right='on',
		#     length=10)
		# plt.tick_params(
		# 	which='minor', 
		# 	bottom='on', 
		# 	top='on',
		# 	left='on',
		# 	right='on',
		# 	length=5)
		# for i in range(len(SN_Array)):
		#     plt.plot(SN_Array[i].wavelength[SN_Array[i].x1:SN_Array[i].x2], SN_Array[i].flux[SN_Array[i].x1:SN_Array[i].x2], color = '#7570b3', alpha = .5)
		# plt.plot(template.wavelength[template.x1:template.x2], template.flux[template.x1:template.x2], 'k', linewidth = 6)
		# plt.ylabel('Relative Flux', fontsize = 30)
		# plt.xlabel('Rest Wavelength ' + "($\mathrm{\AA}$)", fontsize = 30)
		# # "SELECT * from Supernovae inner join Photometry ON Supernovae.SN = Photometry.SN where phase >= -3 and phase <= 3 and morphology >= 9"
		# plt.savefig('../../Paper_Drafts/scaled.pdf', dpi = 300, bbox_inches = 'tight')
		# plt.show()
		# raise TypeError

	#create bootstrap composites
	else:
		scales  = []
		print "Bootstrapping"
		# samples = int (raw_input("# of samples:"))
		samples = 100
		# low_conf, up_conf = bootstrapping(SN_Array, samples, scales, template, iters, medmean)
		template.low_conf, template.up_conf, boots = bootstrapping(SN_Array, samples, scales, template, iters, medmean)
		up_diff = template.up_conf - template.flux
		low_diff = template.flux - template.low_conf
		template_var = (.5*(up_diff + low_diff))**2.

		template.ivar = 1./template_var
		template.ivar[0:template.x1] = 0.
		template.ivar[template.x2:] = 0.

	# non_zero_data = np.where(template.flux != 0)
	# if len(non_zero_data) > 0:
	# 	template.x1 = non_zero_data[0]
	# 	template.x2 = non_zero_data[-1]
	# 	template.x2 += 1
	nan_bool_flux = np.isnan(template.flux)
	non_nan_data = np.where(nan_bool_flux == False)
	non_nan_data = np.array(non_nan_data[0])
	if len(non_nan_data) > 0:
		template.x1 = non_nan_data[0]
		template.x2 = non_nan_data[-1]
		template.x2 += 1

	return template, boots
	
def main(Full_query, boot = 'nb', medmean = 1, opt = 'n', save_file = 'n', make_corr=True, multi_epoch=False, selection = 'max_coverage', verbose=True):
	"""Main function. Finds supernovae that agree with user query, prompts user 
		on whether to bootstrap or just create a composite, then does so and stores 
		returns the relevant data for plotting in a table.
	"""
	SN_Array = []

	#Accept SQL query as input and then grab what we need
	print "SQL Query:", Full_query
	SN_Array = grab(Full_query, make_corr=make_corr, multi_epoch=multi_epoch, selection = selection)

	lengths = []
	# bad_files = qspec.bad_files()

	# len_before = len(SN_Array)

	# good_SN_Array = [SN for SN in SN_Array if not is_bad_data(SN, bad_files, bad_ivars)]
	# SN_Array = good_SN_Array
	# print len_before - len(SN_Array), 'spectra with nan ivars removed', len(SN_Array), 'spectra left'

	SN_Array_wo_tell = remove_tell_files(SN_Array)
	print len(SN_Array) - len(SN_Array_wo_tell), 'spectra may have telluric contamination'

	# for SN in SN_Array:
	# 	print SN.name
	# mags = np.sort(mg.ab_mags(SN_Array), axis = 0)
	# for i in range(len(mags)):
	#     print mags[i][0], mags[i][1] 

	#UNCOMMENT FOR COMPARISON PLOT
	# new_arr = []
	# new_arr.append(copy.copy(SN_Array[0]))
	SN_Array = apply_host_corrections(SN_Array, lengths, verbose=verbose)

	# new_arr.append(copy.copy(SN_Array[0]))
	# new_arr[0].flux = new_arr[0].flux*1.e-15
	# new_arr[0].filename = 'renamed'
	# new_arr, scales = optimize_scales(new_arr, new_arr[0], True)
	# fig, ax = plt.subplots(1,1)
	# fig.set_size_inches(10, 8, forward = True)
	# ax.get_yaxis().set_ticks([])
	# plt.rc('font', family='serif')
	# plt.plot(new_arr[0].wavelength[new_arr[0].x1:new_arr[0].x2], new_arr[0].flux[new_arr[0].x1:new_arr[0].x2], linewidth = 2, color = 'r')
	# plt.plot(new_arr[1].wavelength[new_arr[1].x1:new_arr[1].x2], new_arr[1].flux[new_arr[1].x1:new_arr[1].x2], linewidth = 2, color = '#3F5D7D')
	# plt.ylabel('Relative Flux')
	# plt.xlabel('Wavelength ' + "($\mathrm{\AA}$)")
	# plt.savefig('../../Paper_Drafts/host_corr.png', dpi = 300, bbox_inches = 'tight')
	# plt.show()

	temp = [SN for SN in SN_Array if len(SN.flux[np.where(SN.flux!=0)]) == max(lengths)]

	try:
		composite = temp[0]
	except IndexError:
		print "No spectra found"
		exit()

	# spec_bin = spectra_per_bin(SN_Array)

	#finds range of useable data
	template = supernova()
	template = copy.copy(composite)
	template.spec_bin = spectra_per_bin(SN_Array)

	#creates main composite
	i = 0
	scales  = []
	iters = 3
	iters_comp = 3
	if boot == 'b':
		boot = True
	else:
		boot = False
	# plt.figure(num = 2, dpi = 100, figsize = [30, 20], facecolor = 'w')
	# for i in range(len(SN_Array)):
	#     plt.plot(SN_Array[i].wavelength, SN_Array[i].flux)
	# plt.plot(template.wavelength, template.flux, 'k', linewidth = 4)
	# plt.show()

	#for updating one spectrum at a time
	# num_plots = len(SN_Array)
	# for i in range(num_plots):
	# 	sub_sns = copy.copy(SN_Array[0:i+1])
	# 	print SN_Array[i].filename, SN_Array[i].phase, SN_Array[i].source, SN_Array[i].SNR, np.average(SN_Array[i].ivar[SN_Array[i].x1:SN_Array[i].x2])
	# 	optimize_scales(sub_sns, template, True)
	# 	(fluxes, ivars, dm15_ivars, red_ivars, reds, phases, ages, vels, dm15s, 
	# 	 flux_mask, ivar_mask, dm15_mask, red_mask) = mask(sub_sns, boot)
	# 	for j in range(iters_comp):
	# 		SN_Array, scales = optimize_scales(SN_Array, template, False)
	# 		template = average(sub_sns, template, medmean, boot, fluxes, ivars, dm15_ivars, red_ivars, 
	# 						   reds, phases, ages, vels, dm15s, flux_mask, ivar_mask, dm15_mask, red_mask)

	# 	plt.figure(num = 2, dpi = 100, figsize = [30, 15], facecolor = 'w')
	# 	plt.subplot(2,1,1)
	# 	# plt.plot(sub_sns[-1].wavelength, sub_sns[-1].flux)
	# 	for SN in sub_sns:
	# 		plt.plot(SN.wavelength[SN.x1:SN.x2], SN.flux[SN.x1:SN.x2])
	# 	plt.plot(template.wavelength[SN.x1:SN.x2], template.flux[SN.x1:SN.x2], 'k', linewidth = 4)
	# 	plt.subplot(2,1,2)
	# 	# plt.plot(sub_sns[-1].wavelength, sub_sns[-1].ivar)
	# 	for SN in sub_sns:
	# 		plt.plot(SN.wavelength[SN.x1:SN.x2], SN.ivar[SN.x1:SN.x2])
	# 		r = sa.measure_si_ratio(SN.wavelength[SN.x1:SN.x2], SN.flux[SN.x1:SN.x2])
	# 		print 'SN Si Ratio: ', r
	# 	r = sa.measure_si_ratio(template.wavelength[template.x1:template.x2], template.flux[template.x1:template.x2], vexp = .001)
	# 	print 'Comp Si Ratio: ', r
	# 	plt.show()


	template, boots = create_composite(SN_Array, boot, template, medmean)


	return template, SN_Array, boots

if __name__ == "__main__":
	main()
