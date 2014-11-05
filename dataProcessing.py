#(dataProcessing.py)
#Functions to handle data and return to main program in usable format

from calendar import monthrange
from itertools import *

YEAR = 2012 #used to determine number of days per month
COSTS ='costs.dat'
IRRIGATION = 'irrigation.dat'
FLOWS = 'flows.dat'

def costData():
	return monthlyToYearly(map(float,open(COSTS,'r').read().strip().split('\t')),YEAR)

def irrigationData():
	return monthlyToYearly(map(float,open(IRRIGATION,'r').read().strip().split('\t')),YEAR)

def flowData():
	return monthlyToYearly(map(lambda x: flowFormat(*map(float,x.strip().split('\t'))),open(FLOWS,'r').readlines()),YEAR)

def flowDataMeans():
	return monthlyToYearly(map(lambda x: ((float(x[1]),0),(float(x[0]),1.0),(float(x[3]),0)),map(lambda x:  x.strip().split('\t'),open(FLOWS,'r').readlines())),YEAR)

def monthlyToYearly(data,year):
	return list(chain(*[list(repeat(data[i],monthrange(year,i+1)[1])) for i in range(12)]))

def flowFormat(mean,low,med,up):
	feasible = False
	m = 0.5
	u = (mean - m*med - 0.5*low)/(up-low)
	l = 0.5 - u
	if u> 0.5:
		m = 0.4
		u = (mean - m*med - 0.6*low)/(up-low)
		l = 0.6 - u	
	return ((low,l),(med,m),(up,u))