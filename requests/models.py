from django.db import models
from accounts.models import User
from locations.models import City
from core.models import Platform
from brokers.models import BrokerProfile



class QuoteRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('quoted', 'Quoted'),
        ('accepted', 'Accepted'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    customer = models.ForeignKey(User, on_delete=models.CASCADE)

    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True)

    product_name = models.CharField(max_length=255)

    product_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product_name} - {self.customer.username}"
    
    
class QuickRequestTemplate(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.title

class BrokerQuote(models.Model):
    STATUS_CHOICES = (
        ('sent', 'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    quote_request = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE, related_name='quotes')
    broker = models.ForeignKey(BrokerProfile, on_delete=models.CASCADE)

    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_days = models.IntegerField()

    notes = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('quote_request', 'broker')

    def __str__(self):
        return f"{self.broker.business_name} - {self.total_price}"