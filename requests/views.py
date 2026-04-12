import json
from decimal import Decimal, InvalidOperation
import httpx
from urllib.parse import quote as url_quote
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Min, Max
from django.conf import settings
from django.urls import reverse
from brokers.models import BrokerProfile
from requests.models import QuoteRequest, BrokerQuote, QuickRequestTemplate
from reviews.models import Review
from core.models import Platform

# ── API Settings ────────────────────────────────────────────────
GROQ_API_KEY = ""
GROQ_API_URL = ""
GROQ_MODEL = ""
RAPIDAPI_KEY = ""
AMAZON_API_HOST = ""
SHEIN_API_HOST = ""
TEMU_API_HOST = ""

# ════════════════════════════════════════════════════════════════
# Kareem's Views
# ════════════════════════════════════════════════════════════════

def create_request(request):
    if 'user_id' not in request.session or request.session.get('role') != 'customer':
        return redirect(f"/login?next={url_quote(request.get_full_path())}")

    broker_id = request.GET.get('broker_id') or request.POST.get('broker_id')
    selected_broker = None
    if broker_id:
        selected_broker = BrokerProfile.objects.filter(id=broker_id).first()

    if request.method == 'GET' and not selected_broker:
        return redirect(reverse('browse_brokers'))

    templates     = QuickRequestTemplate.objects.all()
    error_message = request.GET.get('error')
    prefill_name  = request.GET.get('prefill_name', '')
    prefill_url   = request.GET.get('prefill_url', '')

    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        notes        = request.POST.get('notes')
        product_url  = request.POST.get('product_url', '')

        if not product_name or not notes:
            return redirect(f"/create?broker_id={broker_id}")

        if not selected_broker:
            return redirect(reverse('browse_brokers'))

        broker_platform  = selected_broker.platforms.select_related('platform').first()
        selected_platform = broker_platform.platform if broker_platform else Platform.objects.first()

        if not selected_platform:
            return redirect(f"/create?broker_id={broker_id}&error={url_quote('No platform available.')}")

        QuoteRequest.objects.create(
            product_name=product_name,
            notes=notes,
            customer_id=request.session['user_id'],
            broker=selected_broker,
            product_url=product_url,
            platform=selected_platform,
            city=selected_broker.city if selected_broker.city else None,
        )
        return redirect('/requests/my')

    context = {
        'templates'      : templates,
        'selected_broker': selected_broker,
        'error_message'  : error_message,
        'prefill_name'   : prefill_name,
        'prefill_url'    : prefill_url,
    }
    return render(request, 'create_request.html', context)


def my_requests(request):
    if 'user_id' not in request.session or request.session.get('role') != 'customer':
        return redirect(f"/login?next={url_quote(request.get_full_path())}")

    customer_requests = QuoteRequest.objects.select_related(
        'platform', 'city', 'broker'
    ).filter(
        customer_id=request.session['user_id']
    ).order_by('-created_at')

    customer_id = request.session['user_id']
    for req in customer_requests:
        assigned_quote = req.sync_assigned_quote_from_request_metadata()
        if assigned_quote is None:
            assigned_quote = BrokerQuote.objects.filter(
                quote_request=req
            ).order_by(
                '-updated_at', '-created_at'
            ).first()

        existing_review = None

        if assigned_quote:
            existing_review = Review.objects.filter(
                customer_id=customer_id,
                broker_quote=assigned_quote,
            ).first()

        req.review_quote_id = assigned_quote.id if assigned_quote else None
        req.can_contact_broker = (
            (req.status or '').lower() == 'accepted'
            and bool(req.broker_id)
            and bool(getattr(req.broker, 'show_whatsapp_after_accept', False))
        )
        req.can_rate_broker = (
            (req.status or '').lower() == 'completed'
            and assigned_quote is not None
            and existing_review is None
        )
        req.has_review = existing_review is not None

    context = {
        'customer_requests': customer_requests,
        'notice_message'   : request.GET.get('notice'),
    }
    return render(request, 'my_requests.html', context)


def edit_request(request, id):
    if 'user_id' not in request.session or request.session.get('role') != 'customer':
        return redirect(f"/login?next={url_quote(request.get_full_path())}")

    request_item = get_object_or_404(QuoteRequest, id=id, customer_id=request.session['user_id'])

    if (request_item.status or '').lower() != 'pending':
        return redirect(f"/requests/my?notice={url_quote('You can only edit a pending request.')}")

    error_message = request.GET.get('error')

    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        notes        = request.POST.get('notes')
        product_url  = request.POST.get('product_url', '')

        if not product_name or not notes:
            return redirect(f"/requests/{id}/edit?error={url_quote('Title and description are required.')}")

        request_item.product_name = product_name
        request_item.notes        = notes
        request_item.save()
        return redirect(f"/requests/my?notice={url_quote('Your request was updated successfully.')}")

    context = {
        'request_item'  : request_item,
        'selected_broker': request_item.broker,
        'error_message' : error_message,
    }
    return render(request, 'edit_request.html', context)


def delete_request(request, id):
    if 'user_id' not in request.session or request.session.get('role') != 'customer':
        return redirect(f"/login?next={url_quote(request.get_full_path())}")

    request_item = get_object_or_404(QuoteRequest, id=id, customer_id=request.session['user_id'])

    if (request_item.status or '').lower() != 'pending':
        return redirect(f"/requests/my?notice={url_quote('You can only delete a pending request.')}")

    if request.method == 'POST':
        request_item.delete()
        return redirect(f"/requests/my?notice={url_quote('Your request was deleted successfully.')}")

    return redirect('/requests/my')


def broker_requests(request):
    if 'user_id' not in request.session or request.session.get('role') != 'broker':
        return redirect(f"/login?next={url_quote(request.get_full_path())}")

    assigned_requests = QuoteRequest.objects.select_related(
        'customer', 'platform', 'city', 'broker'
    ).filter(broker__user_id=request.session['user_id']).order_by('-created_at')

    context = {
        'assigned_requests': assigned_requests,
        'notice_message'   : request.GET.get('notice'),
    }
    return render(request, 'broker_requests.html', context)


def broker_request_details(request, id):
    if 'user_id' not in request.session or request.session.get('role') != 'broker':
        return redirect(f"/login?next={url_quote(request.get_full_path())}")

    request_item = get_object_or_404(
        QuoteRequest.objects.select_related('customer', 'platform', 'city', 'broker'),
        id=id,
        broker__user_id=request.session['user_id']
    )
    broker_profile = get_object_or_404(BrokerProfile, user_id=request.session['user_id'])
    broker_quote = request_item.sync_assigned_quote_from_request_metadata()

    if request.method == 'POST':
        action_type = request.POST.get('action_type')
        current_status = (request_item.status or '').lower()

        if action_type == 'complete':
            if current_status != 'accepted':
                return redirect(f"/requests/broker/{id}?notice={url_quote('Only an accepted request can be marked as completed.')}")

            broker_quote = request_item.sync_assigned_quote_from_request_metadata()
            if not broker_quote or broker_quote.total_price <= 0:
                return redirect(f"/requests/broker/{id}?notice={url_quote('Add a valid suggested price before completing this request.')}")

            request_item.status = 'completed'
            request_item.save()

            if broker_quote.status != 'accepted':
                broker_quote.status = 'accepted'
                broker_quote.save()

            return redirect(f"/requests/broker/{id}?notice={url_quote('The request has been marked as completed.')}")

        if current_status not in {'pending', 'quoted'}:
            return redirect(f"/requests/broker/{id}?notice={url_quote('This request has already been updated.')}")

        if action_type == 'accept':
            delivery_days = request.POST.get('delivery_days', '').strip()
            price = request.POST.get('price', '').strip()

            if not price:
                return redirect(f"/requests/broker/{id}?notice={url_quote('Suggested price is required.')}")

            try:
                price_value = Decimal(price)
            except InvalidOperation:
                return redirect(f"/requests/broker/{id}?notice={url_quote('Suggested price must be a valid number.')}")

            if price_value <= 0:
                return redirect(f"/requests/broker/{id}?notice={url_quote('Suggested price must be greater than 0.')}")

            if not delivery_days:
                return redirect(f"/requests/broker/{id}?notice={url_quote('Delivery days are required.')}")

            try:
                delivery_days_value = int(delivery_days)
            except ValueError:
                return redirect(f"/requests/broker/{id}?notice={url_quote('Delivery days must be a valid number.')}")

            if delivery_days_value <= 0:
                return redirect(f"/requests/broker/{id}?notice={url_quote('Delivery days must be greater than 0.')}")

            broker_quote, created = BrokerQuote.objects.get_or_create(
                quote_request=request_item,
                broker=broker_profile,
                defaults={
                    'total_price': price_value,
                    'delivery_days': delivery_days_value,
                    'status': 'accepted',
                },
            )
            if not created:
                broker_quote.total_price = price_value
                broker_quote.delivery_days = delivery_days_value
                broker_quote.status = 'accepted'
                broker_quote.save()

            request_item.status = 'accepted'
            request_item.save()
            return redirect(f"/requests/broker/{id}?notice={url_quote('The request was accepted successfully.')}")

        if action_type == 'reject':
            broker_quote = BrokerQuote.objects.filter(
                quote_request=request_item,
                broker=broker_profile,
            ).first()
            if broker_quote and broker_quote.status != 'rejected':
                broker_quote.status = 'rejected'
                broker_quote.save()

            request_item.status = 'cancelled'
            request_item.save()
            return redirect(f"/requests/broker/{id}?notice={url_quote('The request was rejected successfully.')}")

    context = {
        'request_item'  : request_item,
        'broker_quote'  : broker_quote,
        'notice_message': request.GET.get('notice'),
    }
    return render(request, 'broker_request_details.html', context)


# ════════════════════════════════════════════════════════════════
# Qais's Views
# ════════════════════════════════════════════════════════════════

def submit_quote(request, id):
    if 'user_id' not in request.session or request.session.get('role') != 'broker':
        return redirect('/login')

    broker = BrokerProfile.objects.get(user_id=request.session['user_id'])
    quote_request = get_object_or_404(QuoteRequest, id=id, broker=broker)

    already_quoted = BrokerQuote.objects.filter(quote_request=quote_request, broker=broker).exists()
    if already_quoted:
        return redirect('/dashboard/')

    price_range  = BrokerQuote.objects.filter(quote_request=quote_request).aggregate(
        min_price=Min('total_price'), max_price=Max('total_price')
    )
    quotes_count = BrokerQuote.objects.filter(quote_request=quote_request).count()

    if request.method == 'POST':
        total_price   = request.POST.get('total_price')
        delivery_days = request.POST.get('delivery_days')
        notes         = request.POST.get('notes')
        error         = None

        if not total_price:
            error = 'Price is required'
        elif float(total_price) <= 0:
            error = 'Price must be greater than 0'
        elif not delivery_days:
            error = 'Delivery days is required'
        elif int(delivery_days) <= 0:
            error = 'Delivery days must be greater than 0'

        if error:
            return render(request, 'requests/submit_quote.html', {
                'quote_request': quote_request, 'price_range': price_range,
                'quotes_count': quotes_count, 'error': error,
            })

        BrokerQuote.objects.create(
            quote_request=quote_request, broker=broker,
            total_price=total_price, delivery_days=delivery_days, notes=notes,
        )
        quote_request.status = 'quoted'
        quote_request.save()
        return redirect('/dashboard/')

    return render(request, 'requests/submit_quote.html', {
        'quote_request': quote_request,
        'price_range'  : price_range,
        'quotes_count' : quotes_count,
    })


def chatbot_page(request):
    if 'user_id' not in request.session or request.session.get('role') != 'customer':
        return redirect('/login')
    return render(request, 'requests/chatbot.html')


@csrf_exempt
def chatbot_search(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if 'user_id' not in request.session:
        return JsonResponse({'error': 'Login required'}, status=401)

    data     = json.loads(request.body)
    message  = data.get('message', '').strip()
    msg_type = data.get('type', 'chat')
    history  = data.get('history', [])

    if not message:
        return JsonResponse({'error': 'Message is required'}, status=400)

    groq_headers = {
        'Authorization': f'Bearer {GROQ_API_KEY}',
        'Content-Type' : 'application/json',
    }

    if msg_type == 'chat':
        system_prompt = '''You are a smart shopping assistant for BrokersHub platform.
Your job is to help customers find the exact product they want through conversation.

RULES:
1. Ask questions step by step to narrow down the product (category → subcategory → brand → model/specs)
2. Keep each response SHORT — one question at a time
3. When you have ENOUGH info to search (specific product name), respond with EXACTLY this format:
   SEARCH: <product name>
   Example: SEARCH: iPhone 15 Pro Max 256GB Black
4. Do NOT search too early — make sure you have brand and model at minimum
5. Reply in the same language the user uses (Arabic or English)
6. Be friendly and conversational

CATEGORIES:
- 📱 Electronics → ask "Are you looking for Phones, Laptops, Headphones, or Cameras?"
- 👗 Fashion → ask "Are you looking for Men, Women, or Kids clothing?"
- 🛍️ Shopping → ask "What type of product are you shopping for?"
- 🏠 Home and Living → ask "Are you looking for Furniture, Kitchen items, Decor, or Bedding?"
- ✈️ Travel → ask "Are you looking for Luggage, Travel accessories, or Clothing?"
- ⚽ Sports → ask "Are you looking for Equipment, Clothing, or Shoes?"'''

        messages_list = [{'role': 'system', 'content': system_prompt}]
        for h in history:
            messages_list.append({'role': h['role'], 'content': h['content']})

        try:
            chat_res = httpx.post(GROQ_API_URL, headers=groq_headers, json={
                'model': GROQ_MODEL, 'messages': messages_list, 'max_tokens': 150,
            }, timeout=10)
            ai_reply = chat_res.json()['choices'][0]['message']['content']
        except Exception as e:
            return JsonResponse({'type': 'chat', 'message': 'What product are you looking for?'})

        if ai_reply.strip().startswith('SEARCH:'):
            product_name = ai_reply.replace('SEARCH:', '').strip()
            return do_search(product_name, message, groq_headers)

        return JsonResponse({'type': 'chat', 'message': ai_reply})

    return do_search(message, message, groq_headers)


def do_search(product_name, original_message, groq_headers):
    amazon_results = []
    amazon_price   = None
    try:
        amazon_res  = httpx.get(
            f'https://{AMAZON_API_HOST}/search-v2',
            headers={'X-RapidAPI-Key': RAPIDAPI_KEY, 'X-RapidAPI-Host': AMAZON_API_HOST},
            params={'q': product_name, 'country': 'us', 'limit': '3'},
            timeout=10
        )
        amazon_data = amazon_res.json()
        if amazon_data.get('status') == 'OK':
            for item in amazon_data.get('data', {}).get('products', [])[:3]:
                price_str = item.get('offer', {}).get('price', '')
                amazon_results.append({
                    'platform': 'Amazon', 'name': item.get('product_title', ''),
                    'price': price_str, 'url': item.get('product_url', ''),
                    'image': item.get('product_photos', [''])[0], 'note': '',
                })
                if not amazon_price and price_str:
                    try: amazon_price = float(price_str.replace('$', '').replace(',', '').strip())
                    except: pass
    except Exception as e:
        print("AMAZON ERROR:", e)

    shein_results = []
    try:
        shein_res  = httpx.post(GROQ_API_URL, headers=groq_headers, json={
            'model': GROQ_MODEL,
            'messages': [
                {'role': 'system', 'content': 'Estimate if this product is sold on Shein and its price. Return ONLY JSON: {"available": true, "price": "$25.99", "note": "Estimated price"} or {"available": false}'},
                {'role': 'user', 'content': f'Product: {product_name}'}
            ], 'max_tokens': 60,
        }, timeout=10)
        shein_data = json.loads(shein_res.json()['choices'][0]['message']['content'])
        if shein_data.get('available'):
            shein_results.append({
                'platform': 'Shein', 'name': product_name,
                'price': shein_data.get('price', 'N/A'),
                'url': f'https://www.shein.com/search?q={product_name.replace(" ", "+")}',
                'image': '', 'note': shein_data.get('note', 'Estimated price'),
            })
    except Exception as e:
        print("SHEIN ERROR:", e)

    temu_results = []
    try:
        temu_res  = httpx.post(GROQ_API_URL, headers=groq_headers, json={
            'model': GROQ_MODEL,
            'messages': [
                {'role': 'system', 'content': 'Estimate if this product is sold on Temu and its price (usually 30-60% cheaper than Amazon). Return ONLY JSON: {"available": true, "price": "$15.99", "note": "Estimated price"} or {"available": false}'},
                {'role': 'user', 'content': f'Product: {product_name}. Amazon price: ${amazon_price or "unknown"}'}
            ], 'max_tokens': 60,
        }, timeout=10)
        temu_data = json.loads(temu_res.json()['choices'][0]['message']['content'])
        if temu_data.get('available'):
            temu_results.append({
                'platform': 'Temu', 'name': product_name,
                'price': temu_data.get('price', 'N/A'),
                'url': f'https://www.temu.com/search?q={product_name.replace(" ", "+")}',
                'image': '', 'note': temu_data.get('note', 'Estimated price'),
            })
    except Exception as e:
        print("TEMU ERROR:", e)

    all_results = amazon_results + shein_results + temu_results

    if all_results:
        try:
            analyze_res = httpx.post(GROQ_API_URL, headers=groq_headers, json={
                'model': GROQ_MODEL,
                'messages': [
                    {'role': 'system', 'content': 'Smart shopping assistant. Give a short friendly summary. Mention cheapest option. Note Shein/Temu are estimated prices. Max 2 sentences. Same language as user.'},
                    {'role': 'user', 'content': f'Searched: {original_message}\nResults: {json.dumps(all_results, ensure_ascii=False)}'}
                ], 'max_tokens': 150,
            }, timeout=10)
            ai_summary = analyze_res.json()['choices'][0]['message']['content']
        except:
            ai_summary = f"Found {len(all_results)} results for '{product_name}'."
    else:
        ai_summary = f"Sorry, I couldn't find results for '{product_name}'."

    return JsonResponse({
        'type': 'search', 'product_name': product_name,
        'ai_summary': ai_summary, 'results': all_results,
        'has_results': len(all_results) > 0,
    })
