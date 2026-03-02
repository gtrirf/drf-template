from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser, UserRole


# ---------------------------------------------------------------------------
# User serializers
# ---------------------------------------------------------------------------

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'username', 'phone_number', 'avatar', 'full_name', 'role', 'is_active']
        read_only_fields = ['id']


class UserDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'username', 'phone_number',
            'first_name', 'last_name', 'full_name',
            'avatar', 'role', 'is_active', 'date_joined', 'updated_at',
        ]
        read_only_fields = ['id', 'date_joined', 'updated_at']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'first_name', 'last_name', 'phone_number', 'avatar']


# ---------------------------------------------------------------------------
# Ro'yxatdan o'tish — 3 qadam
# ---------------------------------------------------------------------------

class RegisterStep1SendOTPSerializer(serializers.Serializer):
    """1-qadam: emailga OTP kodi yuborish."""
    email = serializers.EmailField()

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Bu email allaqachon ro'yxatdan o'tgan.")
        return value


class RegisterStep1VerifySerializer(serializers.Serializer):
    """1-qadam: OTP kodni tasdiqlash."""
    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)


class RegisterStep2Serializer(serializers.ModelSerializer):
    """2-qadam: profil ma'lumotlarini ixtiyoriy to'ldirish."""

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'avatar', 'phone_number']
        extra_kwargs = {
            'username': {'required': False},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'avatar': {'required': False},
            'phone_number': {'required': False},
        }


class SetPasswordSerializer(serializers.Serializer):
    """3-qadam: yangi parol o'rnatish (eski parol talab qilinmaydi)."""
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Parollar mos kelmaydi.'})
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """Parol o'zgartirish: eski parol tasdiqlanib, yangi parol o'rnatiladi."""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError("Joriy parol noto'g'ri.")
        return value

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Parollar mos kelmaydi.'})
        return data


# ---------------------------------------------------------------------------
# Login serializer
# ---------------------------------------------------------------------------

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)

    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user = UserDetailSerializer(read_only=True)

    def validate(self, data):
        user = authenticate(
            request=self.context.get('request'),
            username=data['email'],
            password=data['password'],
        )
        if not user:
            raise serializers.ValidationError("Email yoki parol noto'g'ri.")
        if not user.is_active:
            raise serializers.ValidationError("Akkaunt faol emas. Emailingizni tasdiqlang.")
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserDetailSerializer(user).data,
        }


# ---------------------------------------------------------------------------
# Parol tiklash serializers
# ---------------------------------------------------------------------------

class ForgotPasswordRequestSerializer(serializers.Serializer):
    """Parolni tiklash: email orqali OTP kodi so'rash."""
    email = serializers.EmailField()

    def validate_email(self, value):
        user = CustomUser.objects.filter(email=value).first()
        if not user:
            raise serializers.ValidationError("Bu email bilan foydalanuvchi topilmadi.")
        self.context['user'] = user
        return value


class ForgotPasswordVerifySerializer(serializers.Serializer):
    """Parolni tiklash: OTP kodi va yangi parolni yuborish."""
    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Parollar mos kelmaydi.'})
        return data
