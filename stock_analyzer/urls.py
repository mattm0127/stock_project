from django.urls import path, include
from . import views

urlpatterns = [
        path('account/', include('django.contrib.auth.urls')), # contains name='login'
        path('signup/', views.SignUp.as_view(), name='signup'),
        path('logout/', views.logout_request, name='logout'),
        path('', views.homepage, name='home'),
        path('hub/', views.hub_view, name='hub'),
        path('stock/', views.get_stock_view, name='get_stock'),
        path('tickers/', views.TickerListView.as_view(), name='tickers'),
        path('tickers/<str:stock_ticker>/five_year/', views.individual_fiveyear_view, name='five_year'),
        path('tickers/<str:stock_ticker>/five_year_split/', views.individual_split_view, name='five_year_split'),
        path("compare/", views.compare_tickers_view, name='compare_select'),
        ]