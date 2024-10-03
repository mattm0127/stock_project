from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from .models import CompanyTicker, StockDataframe
from .forms import TickerInputForm
from stock_project import settings

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import plotly as ply
import plotly.express as px
import plotly.io as pio
from pathlib import Path

# Functions for Views
def get_stock_df(stock_ticker):
    ticker = CompanyTicker.objects.get(stock_ticker=stock_ticker)
    stocks = StockDataframe.objects.filter(stock_ticker_id=ticker.id).values()
    df = pd.DataFrame(stocks)
    return df

def check_company_tickers(request, form):
    tickers = CompanyTicker.objects.values('stock_ticker')
    ticker_list = [tickers[x]['stock_ticker'] for x in range(len(tickers))] # Ensures Ticker is not already in database.
    if form.cleaned_data['stock_ticker'] in ticker_list: # If so returns a new blank form
        return True
    else:
        return False

# Views
class SignUp(CreateView):
    form_class = UserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy('login')

class TickerView(LoginRequiredMixin, ListView):
    model = CompanyTicker
    template_name = 'stock_analyzer/ticker_list.html'

def homepage(request):
    return render(request, 'stock_analyzer/home.html')

@login_required 
def get_stock_view(request):
    """Builds 52 week data into StockDatabase, creates graph and adds graph path to CompanyTicker object"""
    if request.method == "POST":
        form = TickerInputForm(request.POST)
        if form.is_valid():
            if check_company_tickers(request, form):
                return render(request, 'stock_analyzer/add_stock.html', {'form': TickerInputForm()})
            stock = yf.Ticker(form.cleaned_data['stock_ticker'])
            df = stock.history('5y', '1d')
            if len(df) == 0:
                return render(request, 'stock_analyzer/add_stock.html', {'form': TickerInputForm()})
            ct = CompanyTicker()
            ct.stock_ticker = form.cleaned_data['stock_ticker']
            ct.save()
            for x in range(len(df)):
                sdf = StockDataframe()
                sdf.build_database(form, df, x)
        return redirect('tickers')              
    else:
        form = TickerInputForm()
    return render(request, 'stock_analyzer/add_stock.html', {'form': form})

@login_required
def individual_fiveyear_view(request, stock_ticker):
    title = f'Five Year Data for {str(stock_ticker).upper()}'
    df = get_stock_df(stock_ticker)
    plot = px.line(df, x='date', y='close', title=title)
    graph = plot.to_html(full_html=False)
    context = {'graph': graph}
    return render(request, 'stock_analyzer/stock_graph.html', context)

@login_required
def individual_split_view(request, stock_ticker):
    df = get_stock_df(stock_ticker)
    df['year'] = df.date.apply(lambda x: x.strftime('%Y'))
    year_list = list(df.year.unique())
    yearly_dataframes = []
    for year in year_list:
        year_df = df[df.year == year]
        yearly_dataframes.append(year_df)

    context = {}
    for x in range(len(yearly_dataframes)):
        df_year = yearly_dataframes[x].year.iloc[0]
        title = f'{df_year} Data for {stock_ticker.upper()}'
        plot = px.line(yearly_dataframes[x], x='date', y='close', title=title, height=425,width=750)
        plot.update_layout(yaxis_range=[0, df.close.max()])
        graph = plot.to_html(full_html=False)
        context[f"graph_{x}"] = graph
    return render(request, 'stock_analyzer/split_graph.html', context)

@login_required
def logout_request(request): 
    logout(request)
    return redirect('home')
