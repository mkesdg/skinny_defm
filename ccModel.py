from ConfigParser import ConfigParser
import logging
import logging.config
import pyodbc
import numpy as np
import scipy as sp
import scipy.interpolate as spi
import matplotlib.pyplot as plt
import itertools
import csv

import pdb
import os

#def setup():
# load properties then connect to database
os.chdir(r"M:\RES\Users\mke\forecast\skinny_defm")

conFile = "ccModel.properties"
config = ConfigParser()
config.read(conFile)

# basic settings used throughout model
basedir = config.get("DEFAULT", "basedir")
outdir = config.get("DEFAULT", "outdir")
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

# start of run: refresh fcst.demog_rates table and prepopulate with 0s
curs.execute("EXEC fcst.reset_demog_rates {0}, {1}, {2}".format(scenario_id, base_year, end_year))
conn.commit()

# read in survival rates and determine if they need to be interpolated
sql = config.get("sql", "survival_grouped_in")
curs.execute(sql)
header = [(i[0],i[1]) for i in curs.description]
surv = np.fromiter((tuple(row) for row in curs), dtype=header)

# unique year/sex/ethnicity combos (must be a better way)
inyears = list(set(surv["yr"]))
inyears.sort() # used to interpolate between given values
ntables = set(itertools.izip(surv['yr'], surv['sex'], surv['ethnicity']))
nrows = int(surv.shape[0] / float(len(ntables)))
surv = surv.reshape(len(ntables),nrows)

def constrain_rates(rates):
    """ Constrains input rates to be between 0 and 1.
    Invalid values are interpolated between adjacent acceptable values"""
    good = []
    cnt = 0
    for i, r in enumerate(rates):
        if r > 0 and r <= 1:
            if cnt == 0:
                good.append(r)
            else:
                # linear interpolation for negative points as a list.
                # list includes the first valid number as well
                beg = rates[i - (cnt + 1)]
                end = rates[i]
                l = []
                for c in xrange(cnt + 1):
                    fract = (c + 1) / float(cnt + 1)
                    l.append(beg + ((end - beg) * fract))
                good.extend(l)
                cnt = 0
        else:
            cnt += 1
    return good

# TODO: stick with arrays or at least one shape for list (but makes printing easier)
surv_file = config.get("files", "survival")
res = []
for group in surv:
    year = group[0]["yr"]
    ethnicity = group[0]["ethnicity"]
    sex = group[0]["sex"]
    spline = spi.interp1d(group["age"], group["surv_rate"], kind = "cubic")
    tmp = [[year]*(max_age + 1), [ethnicity]*(max_age + 1), [sex]*(max_age + 1), 
        range(max_age + 1), list(spline(range(max_age + 1)))]
    tmp[4] = constrain_rates(tmp[4])
    res.extend(map(list, zip(*tmp)))
    
with open(os.path.join(basedir, outdir, surv_file), "w") as f:
    writer = csv.writer(f, lineterminator = "\n")
    for row in res:
        writer.writerow(row)
        
# load the given years into the database
curs.execute("EXEC fcst.update_demog_rates {0}, '{1}', '{2}'".format(scenario_id, 
    config.get("columns", "survival"), os.path.join(basedir, outdir, surv_file)))
conn.commit()

# interpolate remaining years
for y in xrange(len(inyears)):
    if y == 0:
        continue
    curs.execute("EXEC fcst.interp_demog_rates {0}, {1}, {2}, '{3}'".format(
        scenario_id, inyears[y - 1], inyears[y], config.get("columns", "survival")))
    conn.commit()
     
 conn.close()

# ma death rate version (calibrate to observed deaths, use future life expectancy) 


 
# deaths/pop method with moving average

# calibrate to observed deaths

# calc future year survival from input life expectancy

# write life tables to excel


    
    
    
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

# trash
for group in surv:
    year = group[0]["yr"]
    ethnicity = group[0]["ethnicity"]
    sex = group[0]["sex"]
    spline = spi.interp1d(group["age"], group["surv_rate"], kind = "cubic")
    res = [[year, ethnicity, sex, age, float(spline(age))] for age in range(max_age + 1)]
    res[4] = constrain_rates(res[4])
    
with open(config.get("files", "survival_load"), "w") as f:
    writer = csv.writer(f, lineterminator = "\n")
    for group in res:
        for row in group:
            writer.writerow(row)