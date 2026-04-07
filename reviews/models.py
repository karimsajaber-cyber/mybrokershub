from django.db import models
from accounts.models import User
from brokers.models import BrokerProfile
from requests.models import BrokerQuote


class Review(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    broker = models.ForeignKey(BrokerProfile, on_delete=models.CASCADE)

    broker_quote = models.OneToOneField(BrokerQuote, on_delete=models.CASCADE)

    rating = models.IntegerField()
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rating} - {self.broker.business_name}"