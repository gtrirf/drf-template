from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    # Ro'yxatdan o'tish (3 qadam)
    RegisterStep1SendOTPView,
    RegisterStep1VerifyView,
    RegisterStep2View,
    RegisterStep3View,
    # Auth
    LoginView,
    LogoutView,
    # Parol
    ChangePasswordView,
    ForgotPasswordRequestView,
    ForgotPasswordVerifyView,
    # Profil
    UserProfileView,
    # Admin
    UserListView,
    UserDetailAdminView,
)

urlpatterns = [
    # --- Ro'yxatdan o'tish (3 qadam) ---
    path('auth/register/send-otp/', RegisterStep1SendOTPView.as_view(), name='register-step1-send-otp'),
    path('auth/register/verify/', RegisterStep1VerifyView.as_view(), name='register-step1-verify'),
    path('auth/register/', RegisterStep2View.as_view(), name='register-step2'),
    path('auth/register/set-password/', RegisterStep3View.as_view(), name='register-step3'),

    # --- Autentifikatsiya ---
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # --- Parol ---
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('auth/forgot-password/', ForgotPasswordRequestView.as_view(), name='forgot-password'),
    path('auth/forgot-password/verify/', ForgotPasswordVerifyView.as_view(), name='forgot-password-verify'),

    # --- Profil ---
    path('users/me/', UserProfileView.as_view(), name='user-profile'),

    # --- Admin: foydalanuvchilar boshqaruvi ---
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', UserDetailAdminView.as_view(), name='user-detail'),
]
