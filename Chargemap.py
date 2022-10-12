#!/usr/bin/env python
# coding: utf-8

# In[7]:


import requests
import pandas as pd
from pandas import json_normalize
import plotly.express as px
import folium
from folium import plugins
import csv
# !pip install openpyxl


# In[2]:


#https://github.com/randyzwitch/streamlit-folium
#uitleg voor folium met streamlit


# In[4]:


maxresults=10000
url_chargemap = ("https://api.openchargemap.io/v3/poi?key=a386a50f-1e5d-4021-baaf-868394bc33e9/?output=json&countrycode=NL&maxresults="+str(maxresults))
response_chargemap = requests.get(url_chargemap)
json_chargemap = response_chargemap.json()
df_chargemap = pd.json_normalize(json_chargemap)

print(df_chargemap.head())
print(df_chargemap.isna().sum())
print(df_chargemap.columns.unique())


# In[5]:


columns = ['Operator', 'Comments', 'DataProvider', 'PercentageSimilarity', 'MediaItems']
for i in columns:
    df_chargemap = df_chargemap[df_chargemap.columns.drop(list(df_chargemap.filter(regex=i)))]
df_chargemap = df_chargemap.dropna(axis=1, how='all')

df_chargemap['AddressInfo.Postcode'] = df_chargemap['AddressInfo.Postcode'].str.replace(r'\D', '', regex=True)


# In[10]:


# download files: https://www.cbs.nl/-/media/_excel/2022/37/2022-cbs-pc6huisnr20210801_buurt.zip
# https://www.cbs.nl/-/media/cbs/onze-diensten/methoden/classificaties/overig/gemeenten-alfabetisch-2022.xlsx
# Website blocks any request to download or read files, has to be done manually


postcode_gemeenten = pd.read_csv('pc6hnr20220801_gwb.csv', sep=';')
postcode_gemeenten = postcode_gemeenten[['PC6', 'Gemeente2022']]
postcode_gemeenten = postcode_gemeenten.sort_values('Gemeente2022', ignore_index=True)
print(postcode_gemeenten)
gemeente_codes = pd.read_excel('Gemeenten alfabetisch 2022.xlsx')
gemeente_codes = gemeente_codes[['Gemeentecode', 'Gemeentenaam']]
gemeente_codes = gemeente_codes.sort_values('Gemeentecode', ignore_index=True)
print(gemeente_codes)


# In[11]:


merged = postcode_gemeenten.merge(gemeente_codes, left_on='Gemeente2022', right_on='Gemeentecode', how='right').drop('Gemeente2022', axis=1)
merged['PC6'] = merged['PC6'].str.replace(r'\D', '', regex=True)
merged = merged.drop_duplicates(subset='PC6').reset_index(drop=True)
merged = merged.sort_values('Gemeentenaam').reset_index(drop=True)
merged = merged.drop('Gemeentecode', axis=1)
print(merged)


# In[12]:


df_chargemap = df_chargemap.merge(merged, left_on='AddressInfo.Postcode', right_on='PC6', how='left')


# In[13]:


#Test om te zien of AddressInfo.Town niet toevallig toch gemeenten bleek te zijn.

unique_chargemap = df_chargemap['AddressInfo.Town'].unique()
gemeenten = gemeente_codes['Gemeentenaam'].unique()
unique_gemeenten = [x for x in unique_chargemap if x in gemeenten]
print(len(unique_gemeenten))

#203 namen zijn ook gemeenten, totaal zijn er 345 gemeenten, dus gebruik merged voor gemeente bepaling.


# In[14]:


map = folium.Map(location = [52.2129919, 5.2793703], zoom_start=7, tiles=None)
base_map = folium.FeatureGroup(name='Basemap', overlay=True, control=False)
folium.TileLayer(tiles='OpenStreetMap').add_to(base_map)
base_map.add_to(map)
All_markers = folium.FeatureGroup(name='all', overlay=False, control=True)
for index, row in df_chargemap.iterrows():
    All_markers.add_child(folium.Marker(location=[row['AddressInfo.Latitude'], row['AddressInfo.Longitude']],
                                                       popup=row['AddressInfo.AddressLine1'])).add_to(map)
for i in merged['Gemeentenaam'].unique():
    globals()['%s' %i] = folium.FeatureGroup(name=i, overlay = False, control = True)
    for index, row in df_chargemap.iterrows():
        if row['Gemeentenaam'] == i:
            globals()['%s' %i].add_child(folium.Marker(location=[row['AddressInfo.Latitude'], row['AddressInfo.Longitude']],
                                                       popup=row['AddressInfo.AddressLine1'])).add_to(map)
folium.LayerControl(position='bottomleft', collapsed=False).add_to(map)
map


# In[17]:


map2 = folium.Map(location = [52.2129919, 5.2793703], zoom_start=7, tiles=None)
base_map = folium.FeatureGroup(name='Basemap', overlay=True, control=False)
folium.TileLayer(tiles='OpenStreetMap').add_to(base_map)
base_map.add_to(map2)
marker_cluster = folium.plugins.MarkerCluster(name='Clusters', overlay=False, control=True).add_to(map2)
for index, row in df_chargemap.iterrows():
    folium.Marker(location=[row['AddressInfo.Latitude'], row['AddressInfo.Longitude']],
                                                       popup=row['AddressInfo.AddressLine1']).add_to(marker_cluster)
    
all_markers = folium.FeatureGroup(name='All markers', overlay=False, control=True)    
map2.add_child(all_markers)
# All_Markers = folium.plugins.FeatureGroupSubGroup(group=all_markers, name=i, overlay = False, control = True)
# for index, row in df_chargemap.iterrows():
# #         if row['Gemeentenaam'] == i:
#             all_markers.add_child(folium.Marker(location=[row['AddressInfo.Latitude'], row['AddressInfo.Longitude']],
#                                                        popup=row['AddressInfo.AddressLine1'])).add_to(map2)


for i in merged['Gemeentenaam'].unique():
    globals()['%s' %i] = folium.plugins.FeatureGroupSubGroup(group=all_markers, name=i, show=False)
    map2.add_child(globals()['%s' %i])
    for index, row in df_chargemap.iterrows():
        if row['Gemeentenaam'] == i:
            globals()['%s' %i].add_child(folium.Marker(location=[row['AddressInfo.Latitude'], row['AddressInfo.Longitude']],
                                                       popup=row['AddressInfo.AddressLine1'])).add_to(map2)
folium.LayerControl(position='bottomleft', collapsed=False).add_to(map2)
map2


# In[18]:


map3 = folium.Map(location = [52.2129919, 5.2793703], zoom_start=7, tiles=None)
base_map = folium.FeatureGroup(name='Basemap', overlay=True, control=False)
folium.TileLayer(tiles='OpenStreetMap').add_to(base_map)
base_map.add_to(map3)
cluster = folium.FeatureGroup(name='Cluster', overlay=False, control=True)
map3.add_child(cluster)
All = folium.plugins.FeatureGroupSubGroup(group=cluster, name='Alle gemeenten', overlay=False, control=True).add_to(map3)
All.add_child(folium.plugins.MarkerCluster(name='Clusters', overlay=False, control=True)).add_to(map3)
for i in merged['Gemeentenaam'].unique():
    globals()['%s' %i] = folium.plugins.FeatureGroupSubGroup(group=cluster, name=i, show=False)
    map3.add_child(globals()['%s' %i])
    for index, row in df_chargemap.iterrows():
        if row['Gemeentenaam'] == i:
            globals()['%s' %i].add_child(folium.Marker(location=[row['AddressInfo.Latitude'], row['AddressInfo.Longitude']],
                                                       popup=row['AddressInfo.AddressLine1'])).add_to(marker_cluster)

all_markers = folium.FeatureGroup(name='Markers', overlay=False, control=True)    
map3.add_child(all_markers)


for i in merged['Gemeentenaam'].unique():
    globals()['%s' %i] = folium.plugins.FeatureGroupSubGroup(group=all_markers, name=i, show=False)
    map3.add_child(globals()['%s' %i])
    for index, row in df_chargemap.iterrows():
        if row['Gemeentenaam'] == i:
            globals()['%s' %i].add_child(folium.Marker(location=[row['AddressInfo.Latitude'], row['AddressInfo.Longitude']],
                                                       popup=row['AddressInfo.AddressLine1'])).add_to(map3)
folium.LayerControl(position='bottomleft', collapsed=False).add_to(map3)
map3


# potentieel voor weghalen/aanpassen uitschieters

# In[17]:


import requests
import urllib.parse
import geopy

#https://geopy.readthedocs.io/en/stable/


#schoonmaken, check coordinaten van adres en geef nieuwe kolom.
# als afstand tussen nieuwe en oude coordinaten groter is dan 200 meter, maak een nieuwe rij voor oude coordinaten
# bepaal straatnaam, huisnummer, postcode en stad

address = 'Chromiumweg 7'
url = 'https://nominatim.openstreetmap.org/search/' + urllib.parse.quote(address) +'?format=json'

response = requests.get(url).json()
print(response[0]["lat"])
print(response[0]["lon"])


# In[ ]:





# In[ ]:





# In[ ]:


https://public.opendatasoft.com/explore/dataset/georef-netherlands-postcode-pc4/table/


# <a style='text-decoration:none;line-height:16px;display:flex;color:#5B5B62;padding:10px;justify-content:end;' href='https://deepnote.com?utm_source=created-in-deepnote-cell&projectId=ecc5ef9a-39f6-413f-b3c7-474ca9679f14' target="_blank">
# <img alt='Created in deepnote.com' style='display:inline;max-height:16px;margin:0px;margin-right:7.5px;' src='data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPHN2ZyB3aWR0aD0iODBweCIgaGVpZ2h0PSI4MHB4IiB2aWV3Qm94PSIwIDAgODAgODAiIHZlcnNpb249IjEuMSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB4bWxuczp4bGluaz0iaHR0cDovL3d3dy53My5vcmcvMTk5OS94bGluayI+CiAgICA8IS0tIEdlbmVyYXRvcjogU2tldGNoIDU0LjEgKDc2NDkwKSAtIGh0dHBzOi8vc2tldGNoYXBwLmNvbSAtLT4KICAgIDx0aXRsZT5Hcm91cCAzPC90aXRsZT4KICAgIDxkZXNjPkNyZWF0ZWQgd2l0aCBTa2V0Y2guPC9kZXNjPgogICAgPGcgaWQ9IkxhbmRpbmciIHN0cm9rZT0ibm9uZSIgc3Ryb2tlLXdpZHRoPSIxIiBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPgogICAgICAgIDxnIGlkPSJBcnRib2FyZCIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoLTEyMzUuMDAwMDAwLCAtNzkuMDAwMDAwKSI+CiAgICAgICAgICAgIDxnIGlkPSJHcm91cC0zIiB0cmFuc2Zvcm09InRyYW5zbGF0ZSgxMjM1LjAwMDAwMCwgNzkuMDAwMDAwKSI+CiAgICAgICAgICAgICAgICA8cG9seWdvbiBpZD0iUGF0aC0yMCIgZmlsbD0iIzAyNjVCNCIgcG9pbnRzPSIyLjM3NjIzNzYyIDgwIDM4LjA0NzY2NjcgODAgNTcuODIxNzgyMiA3My44MDU3NTkyIDU3LjgyMTc4MjIgMzIuNzU5MjczOSAzOS4xNDAyMjc4IDMxLjY4MzE2ODMiPjwvcG9seWdvbj4KICAgICAgICAgICAgICAgIDxwYXRoIGQ9Ik0zNS4wMDc3MTgsODAgQzQyLjkwNjIwMDcsNzYuNDU0OTM1OCA0Ny41NjQ5MTY3LDcxLjU0MjI2NzEgNDguOTgzODY2LDY1LjI2MTk5MzkgQzUxLjExMjI4OTksNTUuODQxNTg0MiA0MS42NzcxNzk1LDQ5LjIxMjIyODQgMjUuNjIzOTg0Niw0OS4yMTIyMjg0IEMyNS40ODQ5Mjg5LDQ5LjEyNjg0NDggMjkuODI2MTI5Niw0My4yODM4MjQ4IDM4LjY0NzU4NjksMzEuNjgzMTY4MyBMNzIuODcxMjg3MSwzMi41NTQ0MjUgTDY1LjI4MDk3Myw2Ny42NzYzNDIxIEw1MS4xMTIyODk5LDc3LjM3NjE0NCBMMzUuMDA3NzE4LDgwIFoiIGlkPSJQYXRoLTIyIiBmaWxsPSIjMDAyODY4Ij48L3BhdGg+CiAgICAgICAgICAgICAgICA8cGF0aCBkPSJNMCwzNy43MzA0NDA1IEwyNy4xMTQ1MzcsMC4yNTcxMTE0MzYgQzYyLjM3MTUxMjMsLTEuOTkwNzE3MDEgODAsMTAuNTAwMzkyNyA4MCwzNy43MzA0NDA1IEM4MCw2NC45NjA0ODgyIDY0Ljc3NjUwMzgsNzkuMDUwMzQxNCAzNC4zMjk1MTEzLDgwIEM0Ny4wNTUzNDg5LDc3LjU2NzA4MDggNTMuNDE4MjY3Nyw3MC4zMTM2MTAzIDUzLjQxODI2NzcsNTguMjM5NTg4NSBDNTMuNDE4MjY3Nyw0MC4xMjg1NTU3IDM2LjMwMzk1NDQsMzcuNzMwNDQwNSAyNS4yMjc0MTcsMzcuNzMwNDQwNSBDMTcuODQzMDU4NiwzNy43MzA0NDA1IDkuNDMzOTE5NjYsMzcuNzMwNDQwNSAwLDM3LjczMDQ0MDUgWiIgaWQ9IlBhdGgtMTkiIGZpbGw9IiMzNzkzRUYiPjwvcGF0aD4KICAgICAgICAgICAgPC9nPgogICAgICAgIDwvZz4KICAgIDwvZz4KPC9zdmc+' > </img>
# Created in <span style='font-weight:600;margin-left:4px;'>Deepnote</span></a>
