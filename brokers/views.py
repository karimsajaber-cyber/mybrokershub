from django.shortcuts import render ,redirect, get_object_or_404
from .models import BrokerProfile
from django.contrib import messages


def landing_page(request):
    brokers = BrokerProfile.objects.all()[:3]
    
    context = {
        "brokers": brokers,
        "active_brokers": "500+",
        "completed_deals": "10K+",
        "rating": "4.8/5",
        "response_time": "<2h",
    }
    return render(request, "landing_page.html", context)

def about(request):
    return render(request, "about_us.html")


def browse_brokers(request):
    brokers = BrokerProfile.objects.all()

    context = {
        "brokers": brokers
    }

    return render(request, "browse_brokers.html", context)



def broker_profile(request, id):
    broker = get_object_or_404(BrokerProfile, id=id)

    return render(request, "broker_profile.html", {
        "broker": broker
    })
    


def join_broker(request):
    if request.method == "POST":

        name = request.POST.get('name')
        email = request.POST.get('email')
        whatsapp = request.POST.get('whatsapp')

        # VALIDATION (simple as you want)
        if not name or not email or not whatsapp:
            messages.error(request, "All fields are required")
            return redirect('about')

        # مؤقتاً (بدون موديل)
        print("New Broker Request:")
        print(name, email, whatsapp)

        messages.success(request, "Your request has been sent successfully")

        return redirect('about')

    return redirect('about')
