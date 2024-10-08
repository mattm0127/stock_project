from django.db.models.query import QuerySet
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from .models import CompanyTicker, StockDataframe
from .forms import TickerInputForm, TickerCompareForm


import yfinance as yf
import pandas as pd
import plotly.express as px


# Functions for Views

def check_company_tickers(stock_ticker):
    """Checks if the ticker is already stored in the database."""
    tickers = CompanyTicker.objects.values('stock_ticker')
    ticker_list = [tickers[x]['stock_ticker'] for x in range(len(tickers))] # Ensures Ticker is not already in database.
    if stock_ticker in ticker_list: # If so returns a new blank form
        return True
    else:
        return False

def get_stock_df(stock_ticker):
    """Creates the dataframe based off the stock ticker input."""
    ticker = CompanyTicker.objects.get(stock_ticker=str(stock_ticker).lower())
    stocks = StockDataframe.objects.filter(stock_ticker_id=ticker.id).values()
    df = pd.DataFrame(stocks)
    return df

def get_stock_df_yearly(stock_ticker):
    """Create dataframes by year for a specific stock."""
    df = get_stock_df(stock_ticker)
    df['year'] = df.date.apply(lambda x: x.strftime('%Y'))
    year_list = list(df.year.unique())
    yearly_dataframes = [df.close.max()]
    for year in year_list:
        year_df = df[df.year == year]
        yearly_dataframes.append(year_df)
    return yearly_dataframes

def create_five_year_graph(stock_ticker):
    """Plots five years worth of data onto a single graph for a single stock."""
    title = f'Five Year Data for {str(stock_ticker).upper()}'
    df = get_stock_df(stock_ticker)
    plot = px.line(df, x='date', y='close', title=title)
    return plot.to_html(full_html=False)

def create_five_year_split(stock_ticker, yearly_dataframes):
    """Plots the yearly dataframes onto a graph, takes get_stock_df_yearly function as an arg."""
    graphs = []
    for x in range(1, len(yearly_dataframes)):
        title = f"{yearly_dataframes[x].year.iloc[0]} Data for {stock_ticker}"
        plot = px.line(yearly_dataframes[x], x='date', y='close', title=title, height=425,width=750)
        plot.update_layout(yaxis_range=[0, yearly_dataframes[0]])
        graphs.append(plot.to_html(full_html=False))
    return graphs

# Views

def homepage(request):
    return render(request, 'stock_analyzer/home.html')

class SignUp(CreateView):
    """Create a new user form."""
    form_class = UserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy('login')

@login_required
def hub_view(request):
    """Displays the users tracked stocks and portfolio."""
    user = request.user
    user_stocks = list(CompanyTicker.objects.filter(users=user))
    context = {
            'user_stocks': user_stocks,
            }
    return render(request, 'stock_analyzer/hub.html', context=context)

class TickerListView(LoginRequiredMixin, ListView):
    """View list of all available stock tickers."""
    model = CompanyTicker
    template_name = 'stock_analyzer/ticker_list.html'
    
    def get_queryset(self):
        user = self.request.user
        return CompanyTicker.objects.filter(users=user)

@login_required #This still needs to be cleaned up more.
def get_stock_view(request):
    """Builds 52 week data into StockDatabase, creates graph and adds graph path to CompanyTicker object"""
    if request.method == "POST":
        form = TickerInputForm(request.POST)
        if form.is_valid():
            stock_ticker = str(form.cleaned_data['stock_ticker']).lower()
            user = request.user
            if check_company_tickers(request, stock_ticker):
                ct = CompanyTicker()
                ct.add_user(stock_ticker, user)
                return redirect('tickers')
            stock = yf.Ticker(stock_ticker)
            df = stock.history('5y', '1d')
            if len(df) == 0:
                return render(request, 'stock_analyzer/add_stock.html', {'form': TickerInputForm()})
            ct = CompanyTicker()
            ct.stock_ticker = stock_ticker
            ct.save()
            ct.users.add(user)
            for x in range(len(df)):
                sdf = StockDataframe()
                sdf.build_database(stock_ticker, df, x)
        return redirect('tickers')              
    else:
        form = TickerInputForm()
    return render(request, 'stock_analyzer/add_stock.html', {'form': form})

@login_required
def individual_fiveyear_view(request, stock_ticker):
    """Sends single stock five year graph to template"""
    context = {'graph': create_five_year_graph(stock_ticker)}
    return render(request, 'stock_analyzer/stock_graph.html', context)

@login_required 
def individual_split_view(request, stock_ticker):
    """Sends five year data split graphs to template."""
    context = {'graphs': create_five_year_split(stock_ticker, get_stock_df_yearly(stock_ticker))}
    return render(request, 'stock_analyzer/split_graph.html', context=context)

@login_required
def compare_tickers_view(request):
    """Accepts user form input for stocks to compare, creates five year graph, and redirects to compare page."""
    user = request.user
    if request.method == "POST":
        form = TickerCompareForm(request.POST)
        if form.is_valid():
            ticker_list=[form.cleaned_data['ticker1'], form.cleaned_data['ticker2']]
            graphs = []
            for x in range(len(ticker_list)):
                graphs.append(create_five_year_graph(ticker_list[x]))
            return render(request, "stock_analyzer/compare.html", {'graphs': graphs})
    else:
        form = TickerCompareForm()
        form.fields['ticker1'].queryset = CompanyTicker.objects.filter(users=user)
        form.fields['ticker2'].queryset = CompanyTicker.objects.filter(users=user)
        return render(request, "stock_analyzer/choose_compare.html", {'form': form})

@login_required
def logout_request(request): 
    logout(request)
    return redirect('home')
