from django.db import models
from django.contrib.auth import get_user_model
import pandas as pd
import yfinance as yf

User = get_user_model()

class CompanyTicker(models.Model):

    #user = models.ForeignKey(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=20, blank=True, default='')
    stock_ticker = models.CharField(max_length=8, blank=True, default='')
    
    def __str__(self):
        return self.stock_ticker

class StockDataframe(models.Model):

    stock_ticker = models.ForeignKey(CompanyTicker, on_delete=models.CASCADE)
    date = models.DateTimeField(blank=True, null=True)
    open = models.DecimalField(max_digits=20, decimal_places=6, blank=True, null=True)
    high = models.DecimalField(max_digits=20, decimal_places=6, blank=True, null=True)
    low = models.DecimalField(max_digits=20, decimal_places=6, blank=True, null=True)
    close = models.DecimalField(max_digits=20, decimal_places=6, blank=True, null=True)
    volume = models.IntegerField(blank=True, null=True)
    dividends = models.FloatField(max_length=6, blank=True, null=True)
    stock_splits = models.FloatField(max_length=6, blank=True, null=True)
    
    def __str__(self):
        return f"{self.stock_ticker} DF {self.date}"
    
    def build_database(self, form, df, row):

        self.stock_ticker = CompanyTicker.objects.get(stock_ticker=form.cleaned_data['stock_ticker']) # Possibly change this to objects.name(form.cleaned_data['stock_ticker'])
        self.date = df.index[row]
        self.open = df.Open.iloc[row]
        self.high = df.High.iloc[row]
        self.low = df.Low.iloc[row]
        self.close = df.Close.iloc[row]
        self.volume = df.Volume.iloc[row]
        self.dividends = df.Dividends.iloc[row]
        self.stock_splits = df['Stock Splits'].iloc[row]
        self.save()
        return 

