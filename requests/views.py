from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import QuoteRequest , QuickRequestTemplate
from brokers.models import BrokerProfile


def create_request(request):
    
    # if 'user_id' not in request.session:
    #     return redirect('/accounts/login')

    broker_id = request.GET.get('broker_id')
    selected_broker = None

    if broker_id:
        selected_broker = BrokerProfile.objects.filter(id=broker_id).first()

    if request.method == "POST":

        title = request.POST.get('title')
        description = request.POST.get('description')
        broker_id_post = request.POST.get('broker_id')

        # validation 
        if not title or not description:
            messages.error(request, "All fields are required")
            return redirect(request.path + f"?broker_id={broker_id}")

        broker = None
        if broker_id_post:
            broker = BrokerProfile.objects.filter(id=broker_id_post).first()

        
        QuoteRequest.objects.create(
            user_id=request.session['user_id'],
            title=title,
            description=description,
            broker=broker 
        )

        return redirect('/requests/my')

    context = {
        'selected_broker': selected_broker
    }

    return render(request, 'create_request.html', context)


def create_request(request):

    # if 'user_id' not in request.session:
    #     return redirect('/accounts/login')

    templates = QuickRequestTemplate.objects.all()

    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        notes = request.POST.get('notes')

        if not product_name or not notes:
            return redirect('/requests/create')

        QuoteRequest.objects.create(
            product_name=product_name,
            notes=notes,
            customer_id=request.session['user_id'],
            platform_id=1  # temporal
        )

        return redirect('/requests/my')

    context = {
        'templates': templates
    }

    return render(request, 'create_request.html', context)