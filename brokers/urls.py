from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('about', views.about, name='about'),
    path('brokers', views.browse_brokers, name='browse_brokers'),
    path('broker/<int:id>', views.broker_profile, name='broker_profile'),
    path('join-broker', views.join_broker, name='join_broker'),
]