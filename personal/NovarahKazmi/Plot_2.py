import numpy as np
import matplotlib as mpl
from matplotlib import rc
import matplotlib.pyplot as plt
import math
from pylab import *
import matplotlib.font_manager
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import FuncFormatter

"""
### Tasks
[X] what figures to plot - atm just main light curve plot 
[X] flexible data label 
[X] need to account for spaces in labels
[X] pipe functions
[X] personalizing the plots from the data
[] zoom

[] Write using latex font or similar
[] stacked data (different y axis) 

"""
def main(plot_data_1,plot_data_2,title,image_title,xlabel,ylabel,legend_1,legend_2):
#def main(num_of_plots,plot_data_1,plot_data_2,title,image_title,xlabel,ylabel,legend_1,legend_2):
# re-name variables
	xaxis_1 = plot_data_1[0] 
	yaxis_1 = plot_data_1[1]
	err_p_1 = plot_data_1[2] 
	err_n_1 = plot_data_1[3]
	xaxis_2 = plot_data_2[0] 
	yaxis_2 = plot_data_2[1]
	err_p_2 = plot_data_2[2] 
	err_n_2 = plot_data_2[3]

# Legend parameters, must come before plotting
	params = {'legend.fontsize': 15, 'legend.linewidth':2}
	plt.rcParams.update(params)

	f = figure()
	subplots_adjust(hspace=0.001)

	ax1 = subplot(2,1,1)
	ax1.plot(xaxis_1,yaxis_1,'b',label = legend_1 )
#	ax1.text(1.1, 0.2, r"Plot_1", fontsize=20, color="b")
#	yticks(arange(-0.9, 1.0, 0.4))
	plt.fill_between(xaxis_1,err_p_1,err_n_1,alpha=1.5, edgecolor='#000080', facecolor='#AFEEEE')
	

	ax2 = subplot(2,1,2, sharex=ax1)
	ax2.plot(xaxis_2,yaxis_2,'b',label = legend_2 )
#	ax2.text(1.1, 0.2, r"Plot_2", fontsize=20, color="k")
#	yticks(arange(0.1, 1.0,  0.2))
	plt.fill_between(xaxis_2,err_p_2,err_n_2,alpha=1.5, edgecolor='#006400', facecolor='#98FB98')

	
	xticklabels = ax1.get_xticklabels()+ax2.get_xticklabels()
	setp(xticklabels, visible=False)
	
	#ax1 = subplot(2,1,1) # Create the plot
	#ax2 = subplot(2,1,2) # Create the plot
	#ax1.plot(xaxis_1,yaxis_1,'b',label = legend_1 ) # Read legend labels from files
	#ax2.plot(xaxis_2,yaxis_2,'g',label = legend_2 )

# Error surrounds data
	#plt.fill_between(xaxis_1,err_p_1,err_n_1,alpha=1.5, edgecolor='#000080', facecolor='#AFEEEE')
	#plt.fill_between(xaxis_2,err_p_2,err_n_2,alpha=1.5, edgecolor='#006400', facecolor='#98FB98')


# Remove legend box frame 
	l = legend()
	l.draw_frame(False)
	draw()

#Set the visual range. Automatic range is ugly. 
	xmin = int(float(xaxis_1[0]))
	xmax = int(float(xaxis_2[-1]))
	plt.xlim((xmin,xmax))

#Label the figure and show
	plt.title( title )
	plt.xlabel( xlabel )
	plt.ylabel( ylabel )
	plt.savefig( image_title )

	plt.show()

"""
# axes rect in relative 0,1 coords left, bottom, width, height.  Turn
# off xtick labels on all but the lower plot

f = figure()
subplots_adjust(hspace=0.001)

ax1 = subplot(3,1,1)
ax1.plot(t,s1)
ax1.text(1.1, 0.2, r"Plot_1", fontsize=20, color="b")
yticks(arange(-0.9, 1.0, 0.4))
ylim(-1,1)

ax2 = subplot(3,1,2, sharex=ax1)
ax2.plot(t,s2)
ax2.text(1.1, 0.2, r"Plot_2", fontsize=20, color="k")
yticks(arange(0.1, 1.0,  0.2))
ylim(0,1)

ax3 = subplot(3,1,3, sharex=ax1)
ax3.plot(t,s3)
ax3.text(1.1, 0.2, r"Plot_3", fontsize=20, color="b")
yticks(arange(-0.9, 1.0, 0.4))
ylim(-1,1)


xticklabels = ax1.get_xticklabels()+ax2.get_xticklabels()
setp(xticklabels, visible=False)
"""
"""	if num_of_plots == 1:
		ax1 = subplot(1,1,1) # Create the plot

		ax1.plot(xaxis_1,yaxis_1,'b',label = legend_1 ) # Read legend labels from files
		ax1.plot(xaxis_2,yaxis_2,'g',label = legend_2 )

# Error surrounds data
		plt.fill_between(xaxis_1,err_p_1,err_n_1,alpha=1.5, edgecolor='#000080', facecolor='#AFEEEE')
		plt.fill_between(xaxis_2,err_p_2,err_n_2,alpha=1.5, edgecolor='#006400', facecolor='#98FB98')
"""
#	if num_of_plots == 2:

