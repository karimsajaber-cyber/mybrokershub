from django.shortcuts import render, redirect, get_object_or_404  # Changed: add object lookup helper for edit and delete views.
from django.urls import reverse  # Changed: build named redirects for the broker-first request flow.
from urllib.parse import quote  # Changed: keep URL-safe notice and error messages.

from core.models import Platform  # Changed: keep platform lookup for request creation.
from .models import QuoteRequest, QuickRequestTemplate  # Changed: keep request models available for all request views.
from brokers.models import BrokerProfile  # Changed: keep broker lookup for request pages.


def create_request(request):


    if 'user_id' not in request.session or request.session.get('role') != 'customer':  # Changed: require an authenticated customer before opening the request page.
        return redirect(f"/login?next={quote(request.get_full_path())}")

    broker_id = request.GET.get('broker_id') or request.POST.get('broker_id')

    selected_broker = None
    if broker_id:
        selected_broker = BrokerProfile.objects.filter(id=broker_id).first()

    if request.method == 'GET' and not selected_broker:  # Changed: stop opening the request form without a selected broker.
        return redirect(reverse('browse_brokers'))  # Changed: send the customer to browse brokers first so they can choose who to contact.

    templates = QuickRequestTemplate.objects.all()
    error_message = request.GET.get('error')


    if request.method == 'POST':

        product_name = request.POST.get('product_name')
        notes = request.POST.get('notes')


        if not product_name or not notes:
            return redirect(f"/create?broker_id={broker_id}")

        if not selected_broker:  # Changed: keep POST requests broker-specific as well.
            return redirect(reverse('browse_brokers'))  # Changed: return to broker browsing when no broker context is available.


        broker_platform = selected_broker.platforms.select_related('platform').first()
        selected_platform = broker_platform.platform if broker_platform else Platform.objects.first()

        
        if not selected_platform:
            error_text = quote('No platform available. Please add one.')
            return redirect(f"/create?broker_id={broker_id}&error={error_text}")


        QuoteRequest.objects.create(
            product_name=product_name,
            notes=notes,
            customer_id=request.session['user_id'],
            broker=selected_broker,   
            platform=selected_platform,
            city=selected_broker.city if selected_broker.city else None,
        )

        return redirect('/requests/my')


    context = {
        'templates': templates,
        'selected_broker': selected_broker,
        'error_message': error_message,
    }

    return render(request, 'create_request.html', context)



# MY REQUESTS 

def my_requests(request):

    if 'user_id' not in request.session or request.session.get('role') != 'customer':  # Changed: require an authenticated customer before showing customer requests.
        return redirect(f"/login?next={quote(request.get_full_path())}")

    customer_requests = QuoteRequest.objects.filter(
        customer_id=request.session['user_id']
    ).order_by('-created_at')

    context = {
        'customer_requests': customer_requests,  # Changed: keep exposing only the current customer's requests.
        'notice_message': request.GET.get('notice'),  # Added: show success or restriction notices on the requests page.
    }  # Changed: finish the my requests page context.

    return render(request, 'my_requests.html', context)  # Changed: render the customer requests list page.


def edit_request(request, id):  # Added: let a customer edit their own pending request.
    if 'user_id' not in request.session or request.session.get('role') != 'customer':  # Changed: require an authenticated customer before editing a request.
        return redirect(f"/login?next={quote(request.get_full_path())}")  # Added: preserve the intended destination through login.

    request_item = get_object_or_404(  # Added: load only the current customer's target request.
        QuoteRequest,  # Added: edit works on quote requests only.
        id=id,  # Added: match the requested record id.
        customer_id=request.session['user_id']  # Added: block access to other customers' requests.
    )  # Added: finish the guarded request lookup.

    if (request_item.status or '').lower() != 'pending':  # Changed: block edits unless the request status is pending, even if old data uses different casing.
        notice_text = quote('You can only edit a pending request.')  # Added: prepare the restriction message for redirect.
        return redirect(f"/requests/my?notice={notice_text}")  # Added: send the customer back to their requests list with a notice.

    error_message = request.GET.get('error')  # Added: show edit form validation errors when needed.

    if request.method == 'POST':  # Added: process the submitted edit form.
        product_name = request.POST.get('product_name')  # Added: read the edited request title.
        notes = request.POST.get('notes')  # Added: read the edited request description.

        if not product_name or not notes:  # Added: keep simple validation on the edit form.
            error_text = quote('Title and description are required.')  # Added: prepare the validation message for redirect.
            return redirect(f"/requests/{id}/edit?error={error_text}")  # Added: send the customer back to the edit form with the validation error.

        request_item.product_name = product_name  # Added: update the request title.
        request_item.notes = notes  # Added: update the request description.
        request_item.save()  # Added: persist the edited request changes.

        notice_text = quote('Your request was updated successfully.')  # Added: prepare the success message for redirect.
        return redirect(f"/requests/my?notice={notice_text}")  # Added: return the customer to the requests list after editing.

    context = {  # Added: build template data for the edit request page.
        'request_item': request_item,  # Added: expose the editable request to the template.
        'selected_broker': request_item.broker,  # Added: show which broker this request belongs to.
        'error_message': error_message,  # Added: expose any validation error message to the template.
    }  # Added: finish the edit request page context.

    return render(request, 'edit_request.html', context)  # Added: render the request edit page.


def delete_request(request, id):  # Added: let a customer delete their own pending request.
    if 'user_id' not in request.session or request.session.get('role') != 'customer':  # Changed: require an authenticated customer before deleting a request.
        return redirect(f"/login?next={quote(request.get_full_path())}")  # Added: preserve the intended destination through login.

    request_item = get_object_or_404(  # Added: load only the current customer's target request.
        QuoteRequest,  # Added: delete works on quote requests only.
        id=id,  # Added: match the requested record id.
        customer_id=request.session['user_id']  # Added: block deletion of other customers' requests.
    )  # Added: finish the guarded request lookup.

    if (request_item.status or '').lower() != 'pending':  # Changed: block deletion unless the request status is pending, even if old data uses different casing.
        notice_text = quote('You can only delete a pending request.')  # Added: prepare the restriction message for redirect.
        return redirect(f"/requests/my?notice={notice_text}")  # Added: send the customer back to the requests list with a notice.

    if request.method == 'POST':  # Added: only delete on an explicit POST submission.
        request_item.delete()  # Added: remove the pending request from the database.
        notice_text = quote('Your request was deleted successfully.')  # Added: prepare the success message for redirect.
        return redirect(f"/requests/my?notice={notice_text}")  # Added: return the customer to the requests list after deletion.

    return redirect('/requests/my')  # Added: ignore non-POST delete attempts and return to the requests list.


def broker_requests(request):  # Added: let a broker see only the requests assigned to them.
    if 'user_id' not in request.session or request.session.get('role') != 'broker':  # Added: require an authenticated broker before showing broker requests.
        return redirect(f"/login?next={quote(request.get_full_path())}")  # Added: preserve the intended broker destination through login.

    assigned_requests = QuoteRequest.objects.select_related(  # Added: load related data for the broker request list efficiently.
        'customer',  # Added: include customer data for the broker summary cards.
        'platform',  # Added: include platform data for the broker summary cards.
        'city',  # Added: include city data for the broker summary cards.
        'broker',  # Added: include broker data for the broker summary cards.
    ).filter(  # Added: keep only requests assigned to the logged-in broker.
        broker__user_id=request.session['user_id']  # Added: lock broker requests to the current broker account.
    ).order_by('-created_at')  # Added: show the latest broker requests first.

    context = {  # Added: build the broker request list page context.
        'assigned_requests': assigned_requests,  # Added: expose only this broker's assigned requests to the template.
        'notice_message': request.GET.get('notice'),  # Added: show broker request action notices after accept or reject.
    }  # Added: finish the broker requests context.

    return render(request, 'broker_requests.html', context)  # Added: render the broker-only request list page.


def broker_request_details(request, id):  # Added: let a broker open one assigned request and respond to it.
    if 'user_id' not in request.session or request.session.get('role') != 'broker':  # Added: require an authenticated broker before opening broker request details.
        return redirect(f"/login?next={quote(request.get_full_path())}")  # Added: preserve the intended broker destination through login.

    request_item = get_object_or_404(  # Added: load only the request assigned to the current broker.
        QuoteRequest.objects.select_related('customer', 'platform', 'city', 'broker'),  # Added: include related data needed by the broker details page.
        id=id,  # Added: match the requested record id.
        broker__user_id=request.session['user_id']  # Added: block brokers from opening requests assigned to someone else.
    )  # Added: finish the guarded broker request lookup.

    if request.method == 'POST':  # Added: process broker actions on the request details page.
        if (request_item.status or '').lower() != 'pending':  # Added: block status changes after the broker already acted once.
            notice_text = quote('This request has already been updated.')  # Added: prepare the already-updated notice.
            return redirect(f"/requests/broker/{id}?notice={notice_text}")  # Added: return to the broker details page with a notice.

        action_type = request.POST.get('action_type')  # Added: read whether the broker accepted or rejected the request.

        if action_type == 'accept':  # Added: handle broker acceptance.
            request_item.status = 'accepted'  # Added: mark the request as accepted so the customer can see the broker contact.
            request_item.save()  # Added: persist the accepted status.
            notice_text = quote('The request was accepted successfully.')  # Added: prepare the acceptance notice.
            return redirect(f"/requests/broker/{id}?notice={notice_text}")  # Added: refresh the details page with the acceptance notice.

        if action_type == 'reject':  # Added: handle broker rejection without changing models.
            request_item.status = 'cancelled'  # Added: use the existing cancelled status to represent a rejected request.
            request_item.save()  # Added: persist the rejected status.
            notice_text = quote('The request was rejected successfully.')  # Added: prepare the rejection notice.
            return redirect(f"/requests/broker/{id}?notice={notice_text}")  # Added: refresh the details page with the rejection notice.

    context = {  # Added: build the broker request details page context.
        'request_item': request_item,  # Added: expose the assigned request to the broker template.
        'notice_message': request.GET.get('notice'),  # Added: show broker action notices on the details page.
    }  # Added: finish the broker request details context.

    return render(request, 'broker_request_details.html', context)  # Added: render the broker-only request details page.
