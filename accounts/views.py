from django.shortcuts import render, redirect  # Added: render pages and redirect after auth actions.
from django.contrib.auth import authenticate  # Added: validate login credentials against the custom user model.
from .models import User  # Added: create new customer accounts during registration.


def login_view(request):  # Added: handle customer login before request creation.
    next_url = request.GET.get('next') or request.POST.get('next') or '/'  # Changed: default navbar login back to the landing page instead of the request form.
    error_message = None  # Added: hold any login error for the template.
    customer_auth_flow = next_url.startswith('/create') or next_url.startswith('/requests/my') or '/edit' in next_url or '/delete' in next_url  # Changed: keep customer auth limited to customer request pages and actions.
    show_register = customer_auth_flow  # Changed: only show registration during the customer request flow.
    auth_title = 'Customer Login' if customer_auth_flow else 'Broker Login'  # Added: switch the login heading based on the current auth flow.
    auth_text = 'Login to continue your broker request.' if customer_auth_flow else 'Login with your broker account credentials.'  # Added: switch the helper text based on the current auth flow.

    if request.method == 'POST':  # Added: process the submitted login form.
        username = request.POST.get('username', '').strip()  # Added: read the submitted username safely.
        password = request.POST.get('password', '')  # Added: read the submitted password.
        user = authenticate(request, username=username, password=password)  # Added: let Django verify the credentials.

        expected_role = 'customer' if customer_auth_flow else 'broker'  # Added: require the role that matches the current auth flow.

        if user and user.role == expected_role:  # Changed: allow login only when the account role matches the current auth flow.
            request.session['user_id'] = user.id  # Added: store the logged-in user id for the current project flow.
            request.session['role'] = user.role  # Added: keep the account role in session for future checks.
            request.session['username'] = user.username  # Added: keep a small user label in session.
            return redirect(next_url)  # Added: send the user back to the page they originally wanted.

        if user and user.role != expected_role:  # Added: block accounts that do not match the expected role for this login flow.
            error_message = 'Please use the correct login for this action.'  # Added: explain that the account role does not match this login flow.
        else:  # Added: handle invalid username/password input.
            error_message = 'Invalid username or password.'  # Added: show a simple login failure message.

    context = {  # Added: pass template data for rendering the login form.
        'next': next_url,  # Added: keep the redirect target in the form.
        'error_message': error_message,  # Added: render any login validation message.
        'show_register': show_register,  # Added: tell the template whether it should offer customer registration.
        'auth_title': auth_title,  # Added: expose the role-specific login heading to the template.
        'auth_text': auth_text,  # Added: expose the role-specific helper text to the template.
    }  # Added: finish the template context.

    return render(request, 'login.html', context)  # Added: render the login page.


def register_view(request):  # Added: create a new customer account before sending a request.
    next_url = request.GET.get('next') or request.POST.get('next') or '/create'  # Added: preserve the destination after registration.
    error_message = None  # Added: hold any registration error for the template.

    if request.method == 'POST':  # Added: process the submitted registration form.
        username = request.POST.get('username', '').strip()  # Added: read the chosen username safely.
        email = request.POST.get('email', '').strip()  # Added: read the submitted email address.
        phone = request.POST.get('phone', '').strip()  # Added: read the submitted phone number.
        password = request.POST.get('password', '')  # Added: read the submitted password.
        confirm_password = request.POST.get('confirm_password', '')  # Added: read the repeated password.

        if not username or not email or not phone or not password or not confirm_password:  # Added: require all registration fields.
            error_message = 'All fields are required.'  # Added: show the missing-fields message.
        elif password != confirm_password:  # Added: block mismatched passwords.
            error_message = 'Passwords do not match.'  # Added: show a clear password mismatch message.
        elif User.objects.filter(username=username).exists():  # Added: keep usernames unique.
            error_message = 'This username already exists.'  # Added: explain the duplicate username problem.
        else:  # Added: create the customer account when validation succeeds.
            user = User.objects.create_user(  # Added: create a new customer using Django's password hashing.
                username=username,  # Added: save the submitted username.
                email=email,  # Added: save the submitted email address.
                password=password,  # Added: hash and store the submitted password.
                role='customer',  # Added: force the new account to be a customer.
                phone=phone,  # Added: save the submitted phone number.
            )  # Added: finish user creation.
            request.session['user_id'] = user.id  # Added: log the new customer into the current session.
            request.session['role'] = user.role  # Added: keep the account role in session for future checks.
            request.session['username'] = user.username  # Added: keep a small user label in session.
            return redirect(next_url)  # Added: send the new customer back to the original destination.

    context = {  # Added: pass template data for rendering the registration form.
        'next': next_url,  # Added: keep the redirect target in the form.
        'error_message': error_message,  # Added: render any registration validation message.
    }  # Added: finish the template context.

    return render(request, 'register.html', context)  # Added: render the registration page.


def logout_view(request):  # Added: clear the current customer session when they choose to log out.
    request.session.flush()  # Added: remove all session data including the stored user id.
    return redirect('/')  # Added: send the user back to the landing page after logout.
