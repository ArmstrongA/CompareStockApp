# -*- coding: utf-8 -*-
"""
Created on Fri Feb 11 23:35:44 2022

@author: DELL
"""

# Import the required packages
import pandas as pd
from functools import lru_cache
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, PreText, Select, Div
from bokeh.plotting import figure

# load the list of tickers
import tickers
tickers = tickers.tickers

# Create a function to ensure that a ticker is not compared to itself


def foo(val, lst):
    return [x for x in lst if x != val]

# A function to read and load data
# Note the use of @lru_cache() decorator is to cache the data and speed up reloads
@lru_cache()
def load_ticker(ticker):
    data = pd.read_csv('all_stocks_5yr.csv', parse_dates=['date'])
    data = data.set_index('date')
    data = data[data['Name'] == ticker]
    return pd.DataFrame({ticker: data.close, ticker+'_returns': data.close.diff()})

# A function to create a dataframe for the selected tickers

@lru_cache()
def get_data(t1, t2):
    df1 = load_ticker(t1)
    df2 = load_ticker(t2)
    data = pd.concat([df1, df2], axis=1)
    data = data.dropna()
    data['t1'] = data[t1]
    data['t2'] = data[t2]
    data['t1_returns'] = data[t1+'_returns']
    data['t2_returns'] = data[t2+'_returns']
    return data


# set up plots

source = ColumnDataSource(
    data=dict(date=[], t1=[], t2=[], t1_returns=[], t2_returns=[]))

tools = 'pan,wheel_zoom,xbox_select,reset'

corr = figure(width=400, height=350,
              tools='pan,wheel_zoom,box_select,reset', output_backend='webgl')
corr.diamond('t1_returns', 't2_returns', size=2, source=source, color="red",
             selection_color="orange", alpha=0.6, nonselection_alpha=0.1, selection_alpha=0.4)


time_series1 = figure(width=900, height=200, tools=tools,
                      x_axis_type='datetime', active_drag="xbox_select", output_backend='webgl')
time_series1.line('date', 't1', source=source, color='orange')


time_series2 = figure(width=900, height=200, tools=tools,
                      x_axis_type='datetime', active_drag="xbox_select", output_backend='webgl')
time_series2.x_range = time_series1.x_range
time_series2.line('date', 't2', source=source, color='green')

# set up widgets

stats = PreText(text='', width=500)
ticker1 = Select(value='AAPL', options=foo('GOOG', tickers))
ticker2 = Select(value='GOOG', options=foo('AAPL', tickers))

# Define callbacks

def change_ticker1(attrname, old, new):
    ticker2.options = foo(new, tickers)
    update()


def change_ticker2(attrname, old, new):
    ticker1.options = foo(new, tickers)
    update()


def update(selected=None):
    t1, t2 = ticker1.value, ticker2.value

    df = get_data(t1, t2)
    data = df[['t1', 't2', 't1_returns', 't2_returns']]
    source.data = data

    update_stats(df, t1, t2)

    corr.title.text = '%s returns vs. %s returns' % (t1, t2)
    time_series1.title.text, time_series2.title.text = t1, t2


def update_stats(data, t1, t2):
    stats.text = str(data[[t1, t2, t1+'_returns', t2+'_returns']].describe())


ticker1.on_change('value', change_ticker1)
ticker2.on_change('value', change_ticker2)


def selection_change(attrname, old, new):
    t1, t2 = ticker1.value, ticker2.value
    data = get_data(t1, t2)
    selected = source.selected.indices
    if selected:
        data = data.iloc[selected, :]
    update_stats(data, t1, t2)

source.selected.on_change('indices', selection_change)

# set up layout

# Add a title message to the app

div = Div(
    text="""
        <p>Select two Stocks to compare key Statistics:</p>
        """,
    width=900,
    height=30,
)
app_title = div
widgets = column(ticker1, ticker2, stats)
main_row = row(widgets, corr)
series = column(time_series1, time_series2)
layout = column(app_title, main_row, series)

# initialize the app
update()

curdoc().add_root(layout)
curdoc().title = "Compare Stocks"
