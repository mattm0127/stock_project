from django import forms
from .models import CompanyTicker

class TickerInputForm(forms.Form):
    stock_ticker = forms.CharField(max_length=6)

