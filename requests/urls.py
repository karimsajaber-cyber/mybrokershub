from django.urls import path
from . import views

urlpatterns = [
    path('create', views.create_request, name='create_request'),  # Changed: keep the request creation route.
    path('requests/my', views.my_requests, name='my_requests'),  # Changed: keep the customer requests list route.
    path('requests/broker', views.broker_requests, name='broker_requests'),  # Added: broker-only route for the assigned requests list.
    path('requests/broker/<int:id>', views.broker_request_details, name='broker_request_details'),  # Added: broker-only route for one assigned request details page.
    path('requests/<int:id>/edit', views.edit_request, name='edit_request'),  # Added: customer route for editing a pending request.
    path('requests/<int:id>/delete', views.delete_request, name='delete_request'),  # Added: customer route for deleting a pending request.
]  # Changed: finish the requests URL list.
