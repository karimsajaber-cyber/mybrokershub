from django.urls import path  # Added: define URL routes for the accounts app.
from . import views  # Added: connect account URLs to account views.

urlpatterns = [  # Added: expose the login and register pages.
    path('login', views.login_view, name='login'),  # Added: customer login route.
    path('register', views.register_view, name='register'),  # Added: customer registration route.
    path('logout', views.logout_view, name='logout'),  # Added: customer logout route.
]  # Added: finish the accounts URL list.
