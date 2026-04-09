from django.shortcuts import render ,redirect, get_object_or_404
from .models import BrokerProfile
from core.models import Category
from locations.models import City
from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse

import time #for not letting Mailtrap consider emails as spams
            #  when the site identifies the delay as many emails


def landing_page(request):
    brokers = BrokerProfile.objects.all()
    
    context = {
        "brokers": brokers,
        "active_brokers": "500+",
        "completed_deals": "10K+",
        "rating": "4.8/5",
        "response_time": "<2h",
    }
    return render(request, "landing_page.html", context)

def about(request):

    errors = request.session.pop('form_errors', None)
    old_data = request.session.pop('old_data', None)

    context = {
        'form_errors': errors,
        'old_data': old_data,
    }
    return render(request, 'about_us.html', context)



def browse_brokers(request):

    brokers = BrokerProfile.objects.all()

    context = {
        'brokers': brokers,
        'categories': Category.objects.all(),
        'cities': City.objects.all(),
    }

    return render(request, 'browse_brokers.html', context)


def filter_brokers(request):

    brokers = BrokerProfile.objects.all()

    category_id = request.GET.get('category')
    city_id = request.GET.get('city')
    search = request.GET.get('search')

    # ✅ CATEGORY (correct relation)
    if category_id:
        brokers = brokers.filter(
            platforms__platform__category_id=category_id
        ).distinct()

    # ✅ CITY
    if city_id:
        brokers = brokers.filter(city_id=city_id)

    # ✅ SEARCH
    if search:
        brokers = brokers.filter(
            user__first_name__icontains=search
        ) | brokers.filter(
            user__last_name__icontains=search
        ) | brokers.filter(
            business_name__icontains=search
        )
        brokers = brokers.distinct()

    data = []

    for broker in brokers:

        categories = []

        # ✅ correct accessor
        for bp in broker.platforms.all():
            name = bp.platform.category.name
            if name not in categories:
                categories.append(name)

        data.append({
            'id': broker.id,
            'name': broker.user.first_name + " " + broker.user.last_name,
            'description': broker.description,
            'categories': categories,
            'city': broker.city.name if broker.city else "Not specified",
        })

    return JsonResponse({'brokers': data})


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

        return redirect('about')

    return redirect('about')




def contact_us(request):

    if request.method == 'POST':

        
        name = request.POST.get('name')
        email = request.POST.get('email')
        whatsapp = request.POST.get('whatsapp')
        message = request.POST.get('message')

        errors = {}

        if not name:
            errors['name'] = "Name is required"

        if not email:
            errors['email'] = "Email is required"

        if not whatsapp:
            errors['whatsapp'] = "WhatsApp is required"

        if not message:
            errors['message'] = "Message is required"

        if errors:
            request.session['form_errors'] = errors
            request.session['old_data'] = request.POST
            
            return redirect('about')

        print("New Broker Request:")
        print(name, email, whatsapp)

        
        admin_message = f"""
New Broker Request:

Name: {name}
Email: {email}
WhatsApp: {whatsapp}

Message:
{message}
"""

        send_mail(
            subject="New Broker Request",
            message=admin_message,
            from_email="brokerhub-team@outlook.com",
            recipient_list=["brokerhub-team@outlook.com"],
            fail_silently=False
        )

        
#         auto_reply = f"""
# Hi {name},

# Thank you for your interest in joining BrokersHub.

# We are excited to have professionals like you on our platform.

# Your request has been received successfully, and our team will review it shortly.

# We will contact you as soon as possible.

# Best regards,
# BrokersHub Team
# """
#         time.sleep(1)
#         send_mail(
#             subject="Your Request Received - BrokersHub",
#             message=auto_reply,
#             from_email="brokerhub-team@outlook.com",
#             recipient_list=[email],
#             fail_silently=False
#         )

        messages.success(request, "Your request has been sent successfully")

    return redirect('/about')
