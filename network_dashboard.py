from turtle import title
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import pymongo
import streamlit as st


st.set_page_config(page_title='NETWORK UPTIME AND DOWNTIME', layout="wide")
st.title('Data report on network uptime and outages over time')

airqo = pymongo.MongoClient(
    "mongodb://admin:U%7D%2BBxu4%21%3Eu@34.140.46.94:17773")
prod_airqo = airqo['prod_airqo']

device_uptime = prod_airqo['device_uptime']
network_uptime = prod_airqo['network_uptime']

device_name = device_uptime.distinct('device_name')
selected_device = st.sidebar.selectbox('Device name', device_name)


@st.cache
def load_device_data(device):
    device_data = pd.DataFrame(device_uptime.find({'device_name': device},
                                                  {'device_name': 1, 'channel_id': 1, 'uptime': 1, 'downtime': 1, 'created_at': 1}))
    network_data = pd.DataFrame(network_uptime.find({}))

    network_data.set_index('created_at', inplace=True)

    device_data.set_index('created_at', inplace=True)

    device_uptime_data = device_data.loc[(
        device_data.uptime == 100)]
    device_downtime_data = device_data.loc[(
        device_data.uptime == 0)]

    device_uptime_count = pd.DataFrame(device_uptime_data.groupby(
        device_uptime_data.index.date).count()['uptime'])
    device_downtime_count = pd.DataFrame(device_downtime_data.groupby(
        device_downtime_data.index.date).count()['downtime'])

    device_name_data = device_uptime_count.join(
        device_downtime_count, how='outer').fillna(0).astype(np.int32)
    #device_name_data = device_name_data.add_suffix('_count')
    device_name_data.index = pd.DatetimeIndex(device_name_data.index)
    device_name_data['pct_uptime'] = (
        device_name_data['uptime']/device_name_data.sum(axis=1)*100).round(1)
    device_name_data['pct_downtime'] = 100 - device_name_data['pct_uptime']

    return device_name_data


device_name_data = load_device_data(selected_device)

device_name_data_year = device_name_data.index.year.unique()
selected_year = st.sidebar.selectbox('Year', device_name_data_year)
device_name_data_month_name = device_name_data[device_name_data.index.year ==
                                               selected_year].index.month_name().unique()
device_name_data_month = device_name_data[device_name_data.index.year ==
                                          selected_year].index.month.unique()

device_name_data_month_wrap = dict(
    zip(device_name_data_month_name, device_name_data_month))
selected_month = st.sidebar.radio('Month', device_name_data_month_name)

# Barchart
my_color = ['g', 'r']
fig_bar, axes_bar = plt.subplots(1, 1, figsize=(14, 10))
device_name_data[(device_name_data.index.year == selected_year) & (
    device_name_data.index.month == device_name_data_month_wrap[selected_month])][['uptime', 'downtime']].plot(kind='bar', ax=axes_bar, color=my_color)
axes_bar.yaxis.set_major_locator(MaxNLocator(integer=True))
axes_bar.set_title(
    f'{selected_device} device network uptime and downtime daily count for the month of {selected_month}, {selected_year}', fontsize=20)
plt.tight_layout(pad=5)

# Piechart

device_name_data_months_group = device_name_data.groupby(
    pd.Grouper(freq='M')).sum()[['uptime', 'downtime']]
device_name_data_months_pct = device_name_data_months_group.div(
    device_name_data_months_group.sum(axis=1), axis='rows').round(2)
fig_pie, axes_pie = plt.subplots(1, 1, figsize=(10, 8))
axes_pie.set_title(
    f'{selected_device} device network uptime and downtime percent for the month of {selected_month}, {selected_year}', fontsize=15)
device_name_data_month_pct = device_name_data_months_pct[(device_name_data_months_pct.index.year == selected_year) & (
    device_name_data_months_pct.index.month == device_name_data_month_wrap[selected_month])]

device_name_data_month_pct.T.plot.pie(
    y=device_name_data_month_pct.index[0], colors=['green', 'red'], autopct='%0.1f%%', ax=axes_pie)
axes_pie.yaxis.set_visible(False)


st.write("Daily Uptime and Downtime count for", selected_device, "device")
st.dataframe(device_name_data, height=200, width=800)
st.title('#')
st.title('#')

row_two_col = st.columns(2)
with row_two_col[0]:
    st.pyplot(fig_bar)

with row_two_col[1]:
    st.pyplot(fig_pie)

hide_streamlit_style = """
            <style>
            MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            footer:after {
            content:'Made with Streamlit by Usman'; 
            visibility: visible;
            display: block;
            position: relative;
            #background-color: red;
            padding: 5px;
            top: 2px;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
