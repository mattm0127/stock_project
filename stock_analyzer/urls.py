from django.urls import path, include
from . import views

urlpatterns = [
        path('', views.homepage, name='home'),
        path('account/', include('django.contrib.auth.urls')), # contains name='login'
        path('signup/', views.SignUp.as_view(), name='signup'),
        path('logout/', views.logout_request, name='logout'),
        path('stock/', views.get_stock_view, name='get_stock'),
        path('tickers/', views.TickerView.as_view(), name='tickers'),
        path('tickers/<str:stock_ticker>/five_year/', views.individual_fiveyear_view, name='graph_show'),
        path('tickers/<str:stock_ticker>/five_year_split/', views.individual_split_view, name='split_show'),
        ]