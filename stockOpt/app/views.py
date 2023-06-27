import datetime as dt
import requests
import yfinance as yf
from django.shortcuts import render
from pandas_datareader import data as web


from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices
from pypfopt.expected_returns import mean_historical_return
from pypfopt.risk_models import CovarianceShrinkage

yf.pdr_override()


def index(request):
    ameritrade = 'VGJNUGNOGJYQE9T7YUSPPZAEXNQGSPNG'
    url = 'https://api.tdameritrade.com/v1/instruments'


    if 'compare' in request.POST:
        stock1 = request.POST['stock1']
        stock2 = request.POST.get('stock2', None)
        stock3 = request.POST.get('stock3', None)

        stockData1 = getData(stock=stock1, key=ameritrade, url=url)

        if stock2:
            stockData2 = getData(stock=stock2, key=ameritrade, url=url)
        else:
            stockData2 = None

        if stock3:
            stockData3 = getData(stock=stock3, key=ameritrade, url=url)
        else: 
            stockData3 = None

        results = {
            "stockData1": stockData1,
            "stockData2": stockData2,
            "stockData3": stockData3,
        }
        return render(request, "app/index.html", results)


    elif 'optimize' in request.POST:
        stock1 = request.POST['stock1']
        stock2 = request.POST.get('stock2')
        stock3 = request.POST.get('stock3', None)

        results = optimize(stock1, stock2, stock3)

        return render(request, "app/index.html", results)

    else:
        return render(request, "app/index.html")


def getData(stock, key, url):

    payload = {'apikey': key,
                   'symbol': stock,
                   'projection':'fundamental'}

    # ameritrade data
    results = requests.get(url,params=payload)
    data = results.json()

    todayDate = dt.datetime.today().strftime('%Y-%m-%d')
    close = web.get_data_yahoo(stock, start=todayDate, end=todayDate)
    close = close['Close']

    # FIX CLOSE

    stockData = {
        "stock": data[stock]['fundamental']['symbol'],
        "description": data[stock]['description'],
        "exchange": data[stock]['exchange'],
        "close": round(close, 2),
        "peRatio": round(data[stock]['fundamental']['peRatio'], 2),
        "returnOnEquity": round(data[stock]['fundamental']['returnOnEquity'], 2),
        "high52": round(data[stock]['fundamental']['high52'], 2),
        "netProfitMarginTTM": round(data[stock]['fundamental']['netProfitMarginTTM'], 2),
        "epsTTM": round(data[stock]['fundamental']['epsTTM'], 2),
    }
    return stockData


def optimize(stock1, stock2, stock3):
        portfolio = [stock1, stock2, stock3]

        startDate = '2016-01-01'
        todayDate = dt.datetime.today().strftime('%Y-%m-%d')

        close = web.get_data_yahoo(portfolio, start=startDate, end=todayDate)['Close']

        meanReturns = mean_historical_return(close)
        covarianceMatrix = CovarianceShrinkage(close).ledoit_wolf()

        ef = EfficientFrontier(meanReturns, covarianceMatrix)
        weights = ef.max_sharpe()
        cleaned_weights = ef.clean_weights()
        
        performance = ef.portfolio_performance(verbose=True)

        optimizedStocks = {
            "performance": peformance,
            "cleaned_weights": cleaned_weights,
        }
        
        return optimizedStocks
