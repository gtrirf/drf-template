from django import forms
from django.contrib import admin, messages
from django.shortcuts import render

from .models import CustomUser, UserRole
from .utils import send_bulk_notification
from django.utils.html import format_html

# ---------------------------------------------------------------------------
# Bulk email form
# ---------------------------------------------------------------------------

class SendEmailForm(forms.Form):
    subject = forms.CharField(
        max_length=255,
        label='Mavzu',
        widget=forms.TextInput(attrs={'style': 'width: 100%; max-width: 600px;'}),
    )
    message = forms.CharField(
        label='Xabar matni',
        widget=forms.Textarea(attrs={'rows': 10, 'style': 'width: 100%; max-width: 600px;'}),
    )


# ---------------------------------------------------------------------------
# Admin action
# ---------------------------------------------------------------------------

@admin.action(description='Tanlangan foydalanuvchilarga email yuborish')
def send_bulk_email_action(modeladmin, request, queryset):
    """
    Admin paneldan tanlangan foydalanuvchilarga ommaviy email yuborish.
    Intermediate form sahifasini ko'rsatadi, keyin xabar yuboradi.
    """
    if 'send' in request.POST:
        form = SendEmailForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']

            # Sahifada hidden inputlar orqali yuborilgan user IDlari
            selected_ids = request.POST.getlist(admin.helpers.ACTION_CHECKBOX_NAME)
            users = CustomUser.objects.filter(pk__in=selected_ids)
            emails = [u.email for u in users if u.email]

            result = send_bulk_notification(emails, subject, message)
            msg = f"{result['success']} ta foydalanuvchiga email muvaffaqiyatli yuborildi."
            if result['failed']:
                msg += f" {len(result['failed'])} ta manzilga yuborib bo'lmadi."
                modeladmin.message_user(request, msg, messages.WARNING)
            else:
                modeladmin.message_user(request, msg, messages.SUCCESS)
            return None  # changelist sahifasiga qaytish
    else:
        form = SendEmailForm()

    return render(request, 'admin/users/send_email.html', {
        'title': 'Foydalanuvchilarga Email Yuborish',
        'form': form,
        'queryset': queryset,
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        'opts': modeladmin.model._meta,
    })


# ---------------------------------------------------------------------------
# CustomUser admin
# ---------------------------------------------------------------------------

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['email', 'show_avatar',  'username', 'full_name', 'role', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'username', 'first_name', 'last_name', 'phone_number']
    ordering = ['-date_joined']
    readonly_fields = ['date_joined', 'updated_at', 'last_login', 'show_avatar_large']
    actions = [send_bulk_email_action]

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('email', 'username', 'password'),
        }),
        ('Shaxsiy ma\'lumotlar', {
            'fields': ('first_name', 'last_name', 'phone_number', 'avatar', 'show_avatar_large'),
        }),
        ('Huquqlar va holat', {
            'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Vaqt belgilari', {
            'fields': ('date_joined', 'updated_at', 'last_login'),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'role', 'is_active'),
        }),
    )

    def full_name(self, obj):
        return obj.get_full_name()
    full_name.short_description = 'To\'liq ism'

    def show_avatar(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 35px; height: 35px; border-radius: 50%; object-fit: cover;" />',
                obj.avatar.url
            )
        return "No Image"
    show_avatar.short_description = "Rasm"

    def show_avatar_large(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="max-height: 200px; border-radius: 10px;" />',
                obj.avatar.url
            )
        return "Rasm yuklanmagan"
    show_avatar_large.short_description = "Joriy rasm"