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
def get_stock_df(stock_ticker):
    """Creates the dataframe based off the stock ticker input."""
    ticker = CompanyTicker.objects.get(stock_ticker=str(stock_ticker).lower())
    stocks = StockDataframe.objects.filter(stock_ticker_id=ticker.id).values()
    df = pd.DataFrame(stocks)
    return df

def check_company_tickers(stock_ticker):
    """Checks if the ticker is already stored in the database."""
    tickers = CompanyTicker.objects.values('stock_ticker')
    ticker_list = [tickers[x]['stock_ticker'] for x in range(len(tickers))] # Ensures Ticker is not already in database.
    if stock_ticker in ticker_list: # If so returns a new blank form
        return True
    else:
        return False

def create_five_year_graph(stock_ticker):
    title = f'Five Year Data for {str(stock_ticker).upper()}'
    df = get_stock_df(stock_ticker)
    plot = px.line(df, x='date', y='close', title=title)
    return plot.to_html(full_html=False)

# Views
class SignUp(CreateView):
    """Create a new user form."""
    form_class = UserCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy('login')

class TickerListView(LoginRequiredMixin, ListView):
    """View list of all available stock tickers."""
    model = CompanyTicker
    template_name = 'stock_analyzer/ticker_list.html'
    
    def get_queryset(self):
        user = self.request.user
        return CompanyTicker.objects.filter(users=user)

def homepage(request):
    return render(request, 'stock_analyzer/home.html')

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
    context = {'graph': create_five_year_graph(stock_ticker)}
    return render(request, 'stock_analyzer/stock_graph.html', context)

@login_required # Take the graphing function out of the view
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
def compare_tickers_view(request):
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
