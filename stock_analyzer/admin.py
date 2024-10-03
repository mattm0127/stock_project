from django.contrib import admin
from .models import CompanyTicker, StockDataframe

# Register your models here.
admin.site.register(CompanyTicker)
admin.site.register(StockDataframe)