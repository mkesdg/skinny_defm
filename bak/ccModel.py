from ConfigParser import ConfigParser
import logging
import logging.config
import pyodbc
import numpy as np
import scipy as sp
import scipy.interpolate as spi
import matplotlib.pyplot as plt
import itertools

import pdb
import os

#def setup():
# load properties then connect to database
os.chdir("H:/forecast/skinny_defm")

conFile = "ccModel.properties"
config = ConfigParser()
config.read(conFile)

# basic settings used throughout model
scenario_id = config.getint("DEFAULT", "scenario_id")
base_year = config.getint("DEFAULT", "base_year")
end_year = config.getint("DEFAULT", "end_year")
max_age = config.getint("DEFAULT", "max_age")

logging.config.fileConfig(conFile)
logging.info("Starting Cohort Component Model")

db = dict(config.items('database'))
connstring = """Driver={driver};Server={server};Port={port};Database={database};\
             Trusted_Connection={trusted};Uid={uid};Password={password}""".format(**db)
logging.info("Connecting to {server} using port {port} and database {database}".format(**db))
conn = pyodbc.connect(connstring)
curs = conn.cursor()

# read in survival rates and determine if they need to be interpolated
sql = config.get("sql", "survival_in")
curs.execute(sql)
header = [(i[0],i[1]) for i in curs.description]
surv = np.fromiter((tuple(row) for row in curs), dtype=header)

# unique sex/ethnicity combos (must be a better way)
ntables = set(itertools.izip(surv['sex'], surv['ethnicity']))
nrows = base.shape[1] / float(len(ntables)) 
base = base.reshape(len(ntables),nrows)

# need to collect values, remove negatives, and make sure works for cutoff at 85+
# easier to use array than list (?)
final = []
for group in base:
ethnicity = group[0]["ethnicity"]
sex = group[0]["sex"]
spline = spi.interp1d(group['age'], group['surv_rate'], kind = 'cubic')
res = [[base_year]*(max_age + 1), [ethnicity]*(max_age + 1), [sex]*(max_age + 1), 
    range(max_age + 1), list(spline(range(max_age + 1)))]
    
plt.plot(group['age'], group['surv_rate'], 'o', c='b')
plt.plot(np.arange(0,100,1), spline(np.arange(0,100,1)), 's', c='r')
plt.show()

plt.plot(np.arange(0,100,1), spline(np.arange(0,100,1)))
plt.plot(group['age'], group['surv_rate'], 'o', c='r')
plt.show()
# do spline, but use deaths with option of grouping/kernel after
# assume future year targets are year-specific(?)

#reslist = [[i[0], i[1], i[2], i[3], i[4]] for i in res]
#resarr = np.fromiter(reslist)

conn.close()

if __name__ == "__main__":
    setup()
    
# scraps
# only interpolate base year (?)
b = np.where(surv['yr'] == base_year)
base = surv[:,b]


# write to csv and bulk insert if noticably slow...
    
# want a superclass so common methods can be used for interpolation and writing to excel(?)
# class rate_table