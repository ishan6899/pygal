import base64
from io import BytesIO
import pygal
from pygal.style import Style, DefaultStyle
from yahoo_fin import stock_info as si

from flask import Flask, render_template, Markup, send_file, request
from matplotlib.figure import Figure
from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf
import joblib
from sklearn.preprocessing import PolynomialFeatures 



app = Flask(__name__,template_folder='templates')




custom_style = Style(colors=('#9C27B0', '#00ff00', '#ff0000', '#0000ff'))
cs = Style(colors= ('#FFC107', '#FF5722', '#9C27B0', '#03A9F4', '#8BC34A', '#FF9800', '#E91E63', '#2196F3', '#4CAF50', '#FFEB3B', '#673AB7', '#00BCD4', '#CDDC39', '#9E9E9E', '#607D8B'))
months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']


end = datetime.now()
starttime = datetime(end.year - 1, end.month, end.day)
months = months[end.month:] + months[:end.month]





# ----------------------------------------------------------------------------------------------------
# GRAPH METHODS
# ----------------------------------------------------------------------------------------------------


def actualVsPred(df, ticker):
    name=str(ticker)+'_regression_model.pkl'
    model = joblib.load(name)
    poly = PolynomialFeatures(degree = 4) 
    y = []
    for i in range(9600,9900):
        y.append(((model.predict(poly.fit_transform(np.array([i]).reshape(-1, 1))))[0]))
    line_chart = pygal.Line()
    line_chart.add("Predicted", y)
    line_chart.add("Actual", df['Adj Close'])
    line_chart_data = line_chart.render_data_uri()
    return line_chart_data

def closingPriceGraph(df, ticker):
    line_chart = pygal.Line(x_label_rotation=20, x_labels_major_count=10, show_minor_x_labels=False)
    line_chart.title = "Closing Price Graph"
    line_chart.x_labels = df['Date']
    line_chart.add(ticker, df['Adj Close'])
    line_chart_data = line_chart.render_data_uri()
    return line_chart_data

def volumeGraph(df, ticker):
    Stackedline_chart = pygal.StackedLine(x_label_rotation=20, x_labels_major_count=10, show_minor_x_labels=False, fill = True, style = DefaultStyle)
    Stackedline_chart.title = "Volume Graph"
    Stackedline_chart.x_labels = df['Date']
    Stackedline_chart.add(ticker, df['Volume'])
    Stackedline_chart_data = Stackedline_chart.render_data_uri()
    return Stackedline_chart_data

def maGraph(df, ticker):
    line_chart = pygal.Line(x_label_rotation=20, x_labels_major_count=10, show_minor_x_labels=False, style = cs)
    line_chart.title = "Moving Averages Graph"
    line_chart.x_labels = df['Date']
    ma_day = [10, 20, 50]
    for ma in ma_day:
        column_name = f"MA for {ma} days"
        df[column_name] = df['Adj Close'].rolling(ma).mean()
    x = [None] * 10 + list(df['MA for 10 days'][10:])
    y = [None] * 20 + list(df['MA for 20 days'][20:])
    z = [None] * 50 + list(df['MA for 50 days'][50:])
    line_chart.add('MA for 10 days', x, allow_interruptions=True)
    line_chart.add('MA for 20 days', y, allow_interruptions=True)
    line_chart.add('MA for 50 days', z, allow_interruptions=True)
    line_chart.add('Adj Close', df['Adj Close'], allow_interruptions=True)
    line_chart_data = line_chart.render_data_uri()
    return line_chart_data

def dailyReturn(df, ticker):
    df['Daily Return'] = df['Adj Close'].pct_change()
    df['Daily Return'] = df['Daily Return'].replace(np.nan, 0)
    line_chart = pygal.Line(style=custom_style, fill = True, x_label_rotation=20, x_labels_major_count=10, show_minor_x_labels=False)
    line_chart.title = "Daily Returns"
    line_chart.x_labels = df['Date']
    line_chart.add(ticker, df['Daily Return'], allow_interruptions=True)
    line_chart_data = line_chart.render_data_uri()
    return line_chart_data

def datetimeGraph(df, ticker):
    c = df.groupby(df['Date'].dt.strftime('%B'))['Volume'].mean()
    line_chart = pygal.Bar(style=cs, fill = True, x_label_rotation=20, x_labels_major_count=12, show_minor_x_labels=False,spacing=5)
    line_chart.title = "Monthly Volume"
    k = []
    for i in months:
        k.append(c[i])
    line_chart.x_labels = months
    line_chart.add("Volume averages", k[:-1])
    line_chart_data = line_chart.render_data_uri()
    return line_chart_data

def createGraphs(graphNamesList, ticker, df):
    graphsList = []
    for i in graphNamesList:
        graphsList.append(eval(i + "(df, ticker)"))
    return graphsList





# ----------------------------------------------------------------------------------------------------
# APP ROUTES
# ----------------------------------------------------------------------------------------------------


@app.route("/")
def yoo():
    return render_template('index2.html')


@app.route("/yoo2", methods = ['GET', 'POST'])
def yoo2():
    return render_template('yoo2.html')


@app.route("/interpreted", methods = ['GET', 'POST'])
def interpreted():
    global ticker
    ticker = request.form["company"]
    tick = yf.Ticker(ticker)
    company_name = tick.info['longName']
    df = yf.download(ticker, start=starttime)
    t = si.get_quote_table(ticker)
    df.reset_index(level=0, inplace=True)
    graphNamesList = ["actualVsPred","closingPriceGraph", "volumeGraph", "maGraph", "dailyReturn", "datetimeGraph"]
    graphs = createGraphs(graphNamesList, ticker, df)

    return render_template("yoo2.html", ticker = ticker, t = t, graphs = graphs, company_name = company_name)




if __name__ == "__main__":
    app.run (debug = True)


