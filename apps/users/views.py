import logging

from rest_framework import generics, serializers as drf_serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiResponse,
    inline_serializer,
)

from .models import CustomUser, UserRole
from .permissions import IsRoleAllowed
from .serializers import (
    LoginSerializer,
    SetPasswordSerializer,
    ChangePasswordSerializer,
    ForgotPasswordRequestSerializer,
    ForgotPasswordVerifySerializer,
    UserSerializer,
    UserDetailSerializer,
    UserProfileUpdateSerializer,
    RegisterStep1SendOTPSerializer,
    RegisterStep1VerifySerializer,
    RegisterStep2Serializer,
)
from .utils import (
    send_otp_to_email,
    send_generated_password_email,
    send_password_reset_email,
    verify_otp,
    generate_secure_password,
    grant_set_password_permission,
    consume_set_password_permission,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Qayta ishlatiladigan inline response serializer'lar (drf-spectacular uchun)
# ---------------------------------------------------------------------------

_msg_response = inline_serializer(
    name='MessageResponse',
    fields={'message': drf_serializers.CharField()},
)

_token_response = inline_serializer(
    name='TokenResponse',
    fields={
        'message': drf_serializers.CharField(),
        'access': drf_serializers.CharField(),
        'refresh': drf_serializers.CharField(),
        'user': UserDetailSerializer(),
    },
)

_error_response = inline_serializer(
    name='ErrorResponse',
    fields={'error': drf_serializers.CharField()},
)


# ---------------------------------------------------------------------------
# Ro'yxatdan o'tish — 3 qadam
# ---------------------------------------------------------------------------

class RegisterStep1SendOTPView(APIView):
    """
    POST /auth/register/step1/send-otp/

    1-qadam: emailga OTP tasdiqlash kodi yuborish.
    Email allaqachon ro'yxatdan o'tgan bo'lsa, xato qaytaradi.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Registration'],
        summary='1-qadam: emailga OTP yuborish',
        description=(
            'Email manzilni tekshirib, 6 xonali tasdiqlash kodini yuboradi. '
            'Agar email allaqachon ro\'yxatdan o\'tgan bo\'lsa, xato qaytaradi.'
        ),
        request=RegisterStep1SendOTPSerializer,
        responses={
            200: _msg_response,
            400: _error_response,
            500: _error_response,
        },
    )
    def post(self, request):
        serializer = RegisterStep1SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        if not send_otp_to_email(email):
            return Response(
                {'error': 'Email yuborishda xatolik yuz berdi. Keyinroq urinib ko\'ring.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response({'message': f"Tasdiqlash kodi {email} manziliga yuborildi."})


class RegisterStep1VerifyView(APIView):
    """
    POST /auth/register/step1/verify/

    1-qadam: OTP kodni tasdiqlash.
    Kod to'g'ri bo'lsa, user yaratiladi (generated password bilan), parol emailga yuboriladi,
    va JWT tokenlar qaytariladi (keyingi qadamlar uchun).
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Registration'],
        summary='1-qadam: OTP tasdiqlash va user yaratish',
        description=(
            'OTP kodni tekshiradi. To\'g\'ri bo\'lsa, user yaratiladi va emailga '
            'vaqtinchalik parol yuboriladi. Qaytarilgan JWT tokenlar keyingi '
            'qadamlar (2 va 3) uchun Authorization headerida ishlatiladi.'
        ),
        request=RegisterStep1VerifySerializer,
        responses={
            201: _token_response,
            400: _error_response,
        },
    )
    def post(self, request):
        serializer = RegisterStep1VerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        if not verify_otp(email, code, purpose='verify'):
            return Response(
                {'error': "Kod noto'g'ri yoki muddati o'tgan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if CustomUser.objects.filter(email=email).exists():
            return Response(
                {'error': "Bu email allaqachon ro'yxatdan o'tgan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        generated_password = generate_secure_password()
        user = CustomUser.objects.create_user(
            email=email,
            password=generated_password,
            is_active=True,
            role=UserRole.GUEST,
        )

        send_generated_password_email(email, generated_password)
        grant_set_password_permission(user.id)
        logger.info("User created at step 1: %s", email)

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'message': (
                    "Email tasdiqlandi. Hisobingiz yaratildi. "
                    "Vaqtinchalik parol emailingizga yuborildi."
                ),
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserDetailSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class RegisterStep2View(APIView):
    """
    POST /auth/register/step2/

    2-qadam: profil ma'lumotlarini to'ldirish (barchasi ixtiyoriy).
    Tokenlar Authorization headerida yuborilishi kerak.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Registration'],
        summary='2-qadam: profil ma\'lumotlarini to\'ldirish (ixtiyoriy)',
        description=(
            'username, first_name, last_name, avatar, phone_number maydonlarini '
            'ixtiyoriy to\'ldirib, ma\'lumotlar bazaga saqlaydi. '
            'Barcha maydonlar ixtiyoriy — yuborilmaganlar o\'zgarmaydi.'
        ),
        request=RegisterStep2Serializer,
        responses={
            200: inline_serializer(
                name='Step2Response',
                fields={
                    'message': drf_serializers.CharField(),
                    'user': UserDetailSerializer(),
                },
            ),
            400: _error_response,
        },
    )
    def post(self, request):
        serializer = RegisterStep2Serializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info("Profile updated at step 2: %s", request.user.email)
        return Response({
            'message': "Profil ma'lumotlari saqlandi.",
            'user': UserDetailSerializer(request.user).data,
        })


class RegisterStep3View(APIView):
    """
    POST /auth/register/step3/set-password/

    3-qadam: doimiy parol o'rnatish.
    Eski parol talab qilinmaydi. Muvaffaqiyatli bo'lganda user roli GUEST → USER bo'ladi.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Registration'],
        summary='3-qadam: parol o\'rnatish',
        description=(
            'Doimiy parol o\'rnatadi. Eski parol talab qilinmaydi. '
            'Muvaffaqiyatli bajarilganda foydalanuvchi roli USER ga o\'zgaradi.'
        ),
        request=SetPasswordSerializer,
        responses={
            200: _msg_response,
            400: _error_response,
        },
    )
    def post(self, request):
        if not consume_set_password_permission(request.user.id):
            return Response(
                {'error': "Parol o'rnatish uchun ruxsat yo'q yoki muddati o'tgan. "
                          "Iltimos, email tasdiqlash bosqichidan qaytadan o'ting."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.role = UserRole.USER
        request.user.save(update_fields=['password', 'role'])
        logger.info("Password set at step 3: %s", request.user.email)
        return Response({'message': "Parol muvaffaqiyatli o'rnatildi. Ro'yxatdan o'tish yakunlandi."})


# ---------------------------------------------------------------------------
# Login / Logout
# ---------------------------------------------------------------------------

class LoginView(APIView):
    """
    POST /auth/login/
    Email va parol orqali kirish. Access + Refresh token qaytaradi.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Auth'],
        summary='Tizimga kirish',
        description='Email va parol orqali kirish. Access va Refresh tokenlar qaytaradi.',
        request=LoginSerializer,
        responses={
            200: LoginSerializer,
            400: _error_response,
        },
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class LogoutView(APIView):
    """
    POST /auth/logout/
    Refresh tokenni blacklistga qo'shib, tizimdan chiqadi.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Auth'],
        summary='Tizimdan chiqish',
        description='Refresh tokenni blacklistga qo\'shadi va sеssiyani tugatadi.',
        request=inline_serializer(
            name='LogoutRequest',
            fields={'refresh': drf_serializers.CharField()},
        ),
        responses={
            200: _msg_response,
            400: _error_response,
        },
    )
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token talab qilinadi.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            return Response(
                {'error': "Token yaroqsiz yoki muddati o'tgan."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({'message': 'Tizimdan muvaffaqiyatli chiqdingiz.'})


# ---------------------------------------------------------------------------
# Profil
# ---------------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        tags=['Profile'],
        summary='Mening profilim',
        description='Joriy foydalanuvchi profilini ko\'rish.',
        responses={200: UserDetailSerializer},
    ),
    patch=extend_schema(
        tags=['Profile'],
        summary='Profilni tahrirlash',
        description='Profil ma\'lumotlarini qisman yangilash.',
        request=UserProfileUpdateSerializer,
        responses={200: UserDetailSerializer},
    ),
    put=extend_schema(
        tags=['Profile'],
        summary='Profilni to\'liq yangilash',
        request=UserProfileUpdateSerializer,
        responses={200: UserDetailSerializer},
    ),
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /users/me/  — profilni ko'rish
    PATCH /users/me/ — profilni tahrirlash
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UserProfileUpdateSerializer
        return UserDetailSerializer

    def get_object(self):
        return self.request.user


# ---------------------------------------------------------------------------
# Parol o'zgartirish
# ---------------------------------------------------------------------------

class ChangePasswordView(APIView):
    """
    POST /auth/change-password/
    Autentifikatsiya qilingan foydalanuvchi parolini o'zgartiradi.
    Eski parol talab qilinmaydi.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['Auth'],
        summary='Parol o\'zgartirish',
        description='Eski parolni tasdiqlab, yangi parol o\'rnatadi.',
        request=ChangePasswordSerializer,
        responses={
            200: _msg_response,
            400: _error_response,
        },
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password'])
        logger.info("Password changed: %s", request.user.email)
        return Response({'message': "Parol muvaffaqiyatli o'zgartirildi."})


# ---------------------------------------------------------------------------
# Parolni tiklash
# ---------------------------------------------------------------------------

class ForgotPasswordRequestView(APIView):
    """
    POST /auth/forgot-password/
    Email orqali parolni tiklash kodini yuboradi.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Auth'],
        summary='Parolni tiklash — kod yuborish',
        description='Emailga 6 xonali OTP kodi yuboradi (parolni tiklash uchun).',
        request=ForgotPasswordRequestSerializer,
        responses={
            200: _msg_response,
            400: _error_response,
            500: _error_response,
        },
    )
    def post(self, request):
        serializer = ForgotPasswordRequestSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.context['user']
        if not send_password_reset_email(user):
            return Response(
                {'error': 'Email yuborishda xatolik yuz berdi. Keyinroq urinib ko\'ring.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response({'message': f"Parolni tiklash kodi {user.email} manzilingizga yuborildi."})


class ForgotPasswordVerifyView(APIView):
    """
    POST /auth/forgot-password/verify/
    OTP kodi va yangi parol bilan parolni tiklaydi.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Auth'],
        summary='Parolni tiklash — OTP tasdiqlash va yangi parol',
        description=(
            'OTP kodni va yangi parolni yuboradi. '
            'Kod to\'g\'ri bo\'lsa, parol yangilanadi.'
        ),
        request=ForgotPasswordVerifySerializer,
        responses={
            200: _msg_response,
            400: _error_response,
            404: _error_response,
        },
    )
    def post(self, request):
        serializer = ForgotPasswordVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']

        if not verify_otp(email, code, purpose='reset'):
            return Response(
                {'error': "Kod noto'g'ri yoki muddati o'tgan."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = CustomUser.objects.filter(email=email).first()
        if not user:
            return Response(
                {'error': 'Foydalanuvchi topilmadi.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        user.set_password(new_password)
        user.save(update_fields=['password'])
        logger.info("Password reset for user %s", email)
        return Response({'message': 'Parol muvaffaqiyatli tiklandi.'})


# ---------------------------------------------------------------------------
# Admin: foydalanuvchilar ro'yxati va batafsil ma'lumot
# ---------------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        tags=['Users (Admin)'],
        summary='Barcha foydalanuvchilar ro\'yxati',
        description='Faqat admin va superadmin uchun: barcha foydalanuvchilar ro\'yxati.',
        responses={200: UserSerializer(many=True)},
    ),
)
class UserListView(generics.ListAPIView):
    """
    GET /users/
    Faqat admin/superadmin uchun: barcha foydalanuvchilar ro'yxati.
    """
    permission_classes = [IsAuthenticated, IsRoleAllowed]
    allowed_roles = [UserRole.ADMIN, UserRole.SUPERADMIN]
    serializer_class = UserSerializer
    queryset = CustomUser.objects.all()


@extend_schema_view(
    get=extend_schema(
        tags=['Users (Admin)'],
        summary='Foydalanuvchi ma\'lumotlari',
        responses={200: UserDetailSerializer},
    ),
    patch=extend_schema(
        tags=['Users (Admin)'],
        summary='Foydalanuvchini tahrirlash',
        request=UserDetailSerializer,
        responses={200: UserDetailSerializer},
    ),
    put=extend_schema(
        tags=['Users (Admin)'],
        summary='Foydalanuvchini to\'liq yangilash',
        request=UserDetailSerializer,
        responses={200: UserDetailSerializer},
    ),
    delete=extend_schema(
        tags=['Users (Admin)'],
        summary='Foydalanuvchini o\'chirish',
        responses={204: None},
    ),
)
class UserDetailAdminView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /users/<id>/ — foydalanuvchi ma'lumotlari
    PATCH  /users/<id>/ — foydalanuvchini tahrirlash
    DELETE /users/<id>/ — foydalanuvchini o'chirish
    Faqat admin/superadmin uchun.
    """
    permission_classes = [IsAuthenticated, IsRoleAllowed]
    allowed_roles = [UserRole.ADMIN, UserRole.SUPERADMIN]
    serializer_class = UserDetailSerializer
    queryset = CustomUser.objects.all()
