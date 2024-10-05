from django import forms
from .models import CompanyTicker


class TickerInputForm(forms.Form):
    stock_ticker = forms.CharField(max_length=6)

class TickerCompareForm(forms.Form):
    ticker1 = forms.ModelChoiceField(CompanyTicker.objects.all())
    ticker2 = forms.ModelChoiceField(CompanyTicker.objects.all())
