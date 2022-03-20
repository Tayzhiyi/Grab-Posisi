# -*- coding: utf-8 -*-
"""DSC 2022

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1WGHj2V1kDACdSHXQvDXUJZVeERteQ4ZV
"""

from zipfile import ZipFile

from google.colab import drive
drive.mount('/content/drive')

with ZipFile('drive/MyDrive/grab-posis-city=Singapore.zip', 'r') as zipObj:
  zipObj.extractall('drive/MyDrive/DSC2022')

!pip install dask[dataframe]

#import libraries 
import pandas as pd
import glob
import datetime

import matplotlib.pyplot as plt
import numpy as np

import plotly.express as px
from shapely.geometry import Point

import folium
from folium import plugins
from branca.element import Figure

# latitude and longitude of Singapore
sg_lat = 1.290270
sg_lng = 103.851959

"""List of files (Singapore - GrabPosisi Dataset)

---




"""

list_of_files = glob.glob("/content/drive/MyDrive/DSC2022/city=Singapore/*.parquet")
list_of_files

"""Conversion to take up less RAM


---




"""

def to_category(df, *args):
    for col_name in args:
        df[col_name] = df[col_name].astype("category")
    
def to_float32(df, *args):
    for col_name in args:
        df[col_name] = df[col_name].astype("float32")
        
def to_uint16(df, *args):
    for col_name in args:
        df[col_name] = df[col_name].astype("uint16")
  
def to_int32(df, *args):
    for col_name in args:
      df[col_name] = df[col_name].astype("int32")

def format_datetime(df, col_name):
    # get datetime obj for all timestamps
    dt = df[col_name].apply(datetime.datetime.fromtimestamp)
    
    df["time"] = dt.apply(lambda x: x.time())
    df["day_of_week"] = dt.apply(lambda x: x.weekday())
    df["month"] = dt.apply(lambda x: x.month)
    df["year"] = dt.apply(lambda x: x.year)

"""Creating a dataframe of all the entire dataset

---


"""

def create_df(list):
  df_list = []
  for file in list:
    df_list.append(pd.read_parquet(file))
  df = pd.concat(df_list)
  return df

df = create_df(list_of_files)
df

"""Finding out which OS sends less accurate GPS pings


---


"""

df.groupby('osname').describe()['accuracy']

"""Based on the data above, we can see that the mean accuracy for iOS is 9.38 as compared to that of android which is 5.31. This shows that iOS is around 77% more inaccurate than Android, which can be a possible reason why there may be inaccurate ETA predictions.

Filtering dataframe to accuracy > 4.9 and speed <= 0 for iOS users


Standard for accurate reading <= 4.9 (found online)


---
"""

inaccurate_pings = df[df["accuracy"] > 4.9]
inaccurate_pings = inaccurate_pings[inaccurate_pings["speed"] <= 0]
inaccurate_pings_ios = inaccurate_pings[inaccurate_pings["osname"] == "ios"]
inaccurate_pings_ios

inaccurate_pings_ios_formatted = inaccurate_pings_ios.copy()

"""Convert timestamp to show time, day, month and year"""

format_datetime(inaccurate_pings_ios_formatted, "pingtimestamp")
to_category(inaccurate_pings_ios_formatted, ["trj_id", "driving_mode", "osname"])
to_float32(inaccurate_pings_ios_formatted, ["rawlat", "rawlng", "speed", "accuracy"])
to_uint16(inaccurate_pings_ios_formatted, ["bearing", "day_of_week", "month", "year"])
to_int32(inaccurate_pings_ios_formatted, "pingtimestamp")

inaccurate_pings = inaccurate_pings_ios_formatted

BBox = ((inaccurate_pings["rawlng"].min(), inaccurate_pings["rawlng"].max(),      
         inaccurate_pings["rawlat"].min(), inaccurate_pings["rawlat"].max()))
BBox

inaccurate_pings["Coordinates"] = list(zip(inaccurate_pings["rawlng"], inaccurate_pings["rawlat"]))
inaccurate_pings.head()
inaccurate_pings["Coordinates"] = inaccurate_pings["Coordinates"].apply(Point)
inaccurate_pings.sort_values(by = ["accuracy"], ascending = False)
inaccurate_pings

"""Heat Map of inaccurate GPS Pings

---


"""

df_accuracy42 = inaccurate_pings[['rawlat', 'rawlng']]
df_accuracy42Arr = df_accuracy42.values

fig = Figure(width = 800, height = 800)

# add map to figure
m1 = folium.Map(width = 800, height = 800,
               location = [sg_lat, sg_lng],
               zoom_start = 11, min_zoom = 11, max_zoom = 16)
fig.add_child(m1)

# add heatmap to figure
m1.add_child(plugins.HeatMap(df_accuracy42Arr, radius=15))

m1

"""From the data above, we can see that the inaccurate pings are all highly condensed at a few areas, namely CTE, KPE and MCE. More specifically, the pings are packed around the tunnels of the expressways. Therefore, we can conclude that the tunnels in Singapore could be a reason for inaccurate ETA predictions for users."""