from django.contrib import admin  # Changed: keep Django admin registration available for the custom user admin.
from django.contrib.auth.admin import UserAdmin  # Added: use Django's built-in user admin so passwords are handled correctly.
from .models import User  # Changed: register the existing custom user model with a proper admin class.


@admin.register(User)  # Changed: register the custom user model through the password-safe user admin.
class CustomUserAdmin(UserAdmin):  # Added: make the admin manage the custom user like a real Django auth user.
    model = User  # Added: bind the admin class to the existing custom user model.
    list_display = ('username', 'email', 'role', 'phone', 'is_staff', 'is_active')  # Added: show the most useful broker and auth fields in the admin list.
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')  # Added: let admin filter brokers, customers, and active states easily.
    fieldsets = UserAdmin.fieldsets + (  # Added: extend the default Django user admin fields with the custom role and phone fields.
        ('Additional Info', {'fields': ('role', 'phone')}),  # Added: show the custom user fields in their own admin section.
    )  # Added: finish the custom user fieldset extension.
    add_fieldsets = UserAdmin.add_fieldsets + (  # Added: extend the admin add-user form so new users can be created with custom fields.
        ('Additional Info', {'fields': ('role', 'phone')}),  # Added: allow admin to set role and phone when creating broker accounts.
    )  # Added: finish the custom add-user fieldset extension.
    search_fields = ('username', 'email', 'phone')  # Added: make it easier to find broker and customer users in admin.
    ordering = ('username',)  # Added: keep the admin user list sorted predictably.
