import requests
import pandas as pd
import os
import json
import datetime
from datetime import datetime, timedelta, date
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import numpy as np
load_dotenv()

import warnings
warnings.filterwarnings("ignore")

#function to pull data from systradingmarketdata

def get_marketdata(start_datetime, end_datetime, analysis_group):
    #define the basic parameters of the API call
    baseurl = "https://systradingmarketdataapi.azurewebsites.net/api/"
    url = f"{baseurl}Authentication/request"
    
    payload=f'{{"username": "{os.getenv("MARKETDATA_USER")}", "password": "{os.getenv("MARKETDATA_PWD")}"}}'
    headers = {
      'Authorization': '',
      'Content-Type': 'application/json',
    }
    
    # get the token
    login_response = requests.request("POST", url, headers=headers, data=payload)
    
    params = f"start={start_datetime}&end={end_datetime}&granularity=hours&timeZone=GMT"
    #analysis_group = "1Base_EC%20Generation%20by%20Fuel%20Type"
    group_url = f'{baseurl}AnalysisGroup/AllCurves/{analysis_group}?{params}'

    payload={}
    headers = {
      'Authorization': f'Bearer {login_response.text}',
    }

    response = requests.request("GET", group_url, headers=headers, data=payload)

    #print out the json
    #print(response.text)
    # %%

    power_json = json.loads(response.text)

    # loading hour sequence from the maximum and minimum found - it's not yet clear
    # the logic for the cut off date times.
    max_found_time = max([x['timeSeries'][-1]['date'] for x in power_json['curves']])
    min_found_time = min([x['timeSeries'][0]['date'] for x in power_json['curves']])

    hour_sequence = pd.date_range(start = pd.to_datetime(min_found_time),
                             end = pd.to_datetime(max_found_time),
                             freq = "H")
    # %%
    # create named dataframe from json
    def turn_series_to_df(json_series):
        this_df = pd.DataFrame.from_records(json_series['timeSeries'])
        this_df['date'] = pd.to_datetime(this_df['date'])
        this_df.set_index('date', inplace=True)
        this_df.rename(columns={'value' : json_series['memberName']}, inplace=True)#'name' is an alternative here to memberName
        return(this_df)

    # %%
    # load initial dataset for first time series and fill mising hours

    power_df = turn_series_to_df(power_json['curves'][0])
    power_df = power_df.reindex(hour_sequence)
    power_df.rename_axis("date", axis='index', inplace=True)

    # %%

    for full_series in power_json['curves'][1:]:
        this_df = turn_series_to_df(full_series)
        power_df = pd.merge(power_df,this_df,how='left', left_index=True, right_index=True)

    return power_df


#Pull the data and produce the forecast

dt14 = datetime.today() + timedelta(days = 15)
dt14=datetime(dt14.year,dt14.month,dt14.day)

ce = get_marketdata(datetime(2021,10,1), dt14, 'weather_CEE')


ce = ce.resample(rule='24H', closed='left', label='left', base=5).mean().round(1)
ce['date'] = ce.apply(lambda x: datetime(x.name.year, x.name.month, x.name.day), axis = 1)
ce = ce.set_index('date')
ce = ce.rename(columns = {ce.columns[0]:'obs_Kyiv', ce.columns[1]:'fcst_Kyiv'})
#ce = ce.set_index['date']
comp = pd.DataFrame(index =pd.date_range(start = datetime.today(), end = dt14+ timedelta(days =-1)), columns = ['FCST'])
comp = comp.resample('D').last()
comp['FCST'] = comp.apply(lambda x: ce['fcst_Kyiv'][ce.index==x.name].iloc[0], axis = 1) # if ((x.name >= datetime.today()) & ((x.name - datetime.today()).days<14)) else np.nan

coefs = pd.read_csv('coef.csv')
slope = coefs['slope'].iloc[0]
inter = coefs['intercept'].iloc[0]

comp['DEM_FCST'] = comp['FCST'] * slope  + inter + 3.75

#save the output in the folder
#!!! This part needs to be re-written as the output should be saved in the database
comp.to_csv('output/forecast_'+datetime.today().strftime("%Y-%m-%d")+'.csv')


#compare with the previous forecast

#!!! this part should be re-written as we should pull the previous forecast from the database
prevdate = datetime.now()+timedelta(days = -3) if datetime.today().weekday() == 0 else datetime.now()+timedelta(days = -1)
prevforecast = pd.read_csv('output/forecast_'+prevdate.strftime("%Y-%m-%d")+'.csv', index_col =0)
prevforecast.index = pd.to_datetime(prevforecast.index)
#prevdate = datetime(prevdate.year, prevdate.month, prevdate.day)

#calculate day-on-day change
dod = pd.DataFrame((comp['DEM_FCST'] - prevforecast['DEM_FCST']).dropna())
dod = dod.rename(columns ={'DEM_FCST':'UA'})
dod.index = dod.index.date
dod.loc['Total']= dod.sum(numeric_only=True, axis=0)

comp = comp.rename(columns ={'DEM_FCST':'UA'})
newfcst =pd.DataFrame(comp['UA'])


#Print the results (we should add this to our daily emails)
print('Day-on-day change ('+datetime.today().strftime("%d-%b-%Y") +" vs " +prevdate.strftime("%d-%b-%Y") +') (mcm/d):')
print(dod.round(1))

print('Current forecast (mcm/d):')
print(newfcst.round(1))
