import random
import secrets
import string
import logging

from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

OTP_EXPIRY = 120  # 2 daqiqa (soniyalarda)
OTP_LENGTH = 6


def generate_otp() -> str:
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))


def generate_secure_password(length: int = 12) -> str:
    """Xavfsiz tasodifiy parol generatsiya qilish."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^"
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.isupper() for c in password)
            and any(c.islower() for c in password)
            and any(c.isdigit() for c in password)
            and any(c in "!@#$%^" for c in password)
        ):
            return password


def get_cache_key(email: str, purpose: str) -> str:
    return f"otp:{purpose}:{email}"


def save_otp(email: str, purpose: str, timeout: int = OTP_EXPIRY) -> str:
    code = generate_otp()
    key = get_cache_key(email, purpose)
    cache.set(key, code, timeout=timeout)
    return code


def verify_otp(email: str, code: str, purpose: str) -> bool:
    key = get_cache_key(email, purpose)
    saved_code = cache.get(key)
    if saved_code and saved_code == code:
        cache.delete(key)
        return True
    return False


SET_PASSWORD_EXPIRY = 1800  # 30 daqiqa


def grant_set_password_permission(user_id: int) -> None:
    """Step 1 verify muvaffaqiyatli bo'lgandan so'ng, step 3 uchun bir martalik ruxsat berish."""
    cache.set(f"set_password:{user_id}", True, timeout=SET_PASSWORD_EXPIRY)


def consume_set_password_permission(user_id: int) -> bool:
    """Step 3 da ruxsatni tekshirish va o'chirish (bir martalik — qayta ishlatib bo'lmaydi)."""
    key = f"set_password:{user_id}"
    if cache.get(key):
        cache.delete(key)
        return True
    return False


def send_otp_to_email(email: str) -> bool:
    """Ro'yxatdan o'tishning 1-qadami: faqat email bo'yicha OTP yuborish."""
    code = save_otp(email, purpose='verify')
    subject = "Email manzilingizni tasdiqlang"
    message = (
        f"Salom!\n\n"
        f"Ro'yxatdan o'tishni davom ettirish uchun quyidagi kodni kiriting:\n\n"
        f"  {code}\n\n"
        f"Kod {OTP_EXPIRY // 60} daqiqa davomida amal qiladi.\n\n"
        f"Agar siz ro'yxatdan o'tishni so'ramagan bo'lsangiz, ushbu xabarni e'tiborsiz qoldiring."
    )
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info("Registration OTP sent to %s", email)
        return True
    except Exception as exc:
        logger.error("Failed to send OTP to %s: %s", email, exc)
        return False


def send_generated_password_email(email: str, generated_password: str) -> bool:
    """Yaratilgan foydalanuvchiga vaqtinchalik parolni yuborish."""
    subject = "Hisobingiz yaratildi — Vaqtinchalik parol"
    message = (
        f"Salom!\n\n"
        f"Hisobingiz muvaffaqiyatli yaratildi.\n\n"
        f"Vaqtinchalik parolingiz:\n\n"
        f"  {generated_password}\n\n"
        f"Iltimos, tizimga kirgandan so'ng parolingizni o'zgartiring.\n\n"
        f"Agar siz ro'yxatdan o'tmagan bo'lsangiz, ushbu xabarni e'tiborsiz qoldiring."
    )
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info("Generated password sent to %s", email)
        return True
    except Exception as exc:
        logger.error("Failed to send generated password to %s: %s", email, exc)
        return False


def send_verification_email(user) -> bool:
    """Yangi foydalanuvchi emailini tasdiqlash uchun OTP kodi yuborish."""
    code = save_otp(user.email, purpose='verify')
    subject = "Email manzilingizni tasdiqlang"
    message = (
        f"Salom, {user.get_short_name()}!\n\n"
        f"Email manzilingizni tasdiqlash uchun quyidagi kodni kiriting:\n\n"
        f"  {code}\n\n"
        f"Kod {OTP_EXPIRY // 60} daqiqa davomida amal qiladi.\n\n"
        f"Agar siz ro'yxatdan o'tmagan bo'lsangiz, ushbu xabarni e'tiborsiz qoldiring."
    )
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info("Verification email sent to %s", user.email)
        return True
    except Exception as exc:
        logger.error("Failed to send verification email to %s: %s", user.email, exc)
        return False


def send_password_reset_email(user) -> bool:
    """Parolni tiklash uchun OTP kodi yuborish."""
    code = save_otp(user.email, purpose='reset')
    subject = "Parolni tiklash kodi"
    message = (
        f"Salom, {user.get_short_name()}!\n\n"
        f"Parolingizni tiklash uchun quyidagi kodni kiriting:\n\n"
        f"  {code}\n\n"
        f"Kod {OTP_EXPIRY // 60} daqiqa davomida amal qiladi.\n\n"
        f"Agar siz parol tiklashni so'ramagan bo'lsangiz, ushbu xabarni e'tiborsiz qoldiring."
    )
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )
        logger.info("Password reset email sent to %s", user.email)
        return True
    except Exception as exc:
        logger.error("Failed to send password reset email to %s: %s", user.email, exc)
        return False


def send_bulk_notification(emails: list[str], subject: str, message: str) -> dict:
    """
    Bir nechta foydalanuvchiga ommaviy email yuborish.
    Qaytaradi: {'success': int, 'failed': list[str]}
    """
    success = 0
    failed = []
    for email in emails:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            success += 1
        except Exception as exc:
            logger.error("Bulk email failed for %s: %s", email, exc)
            failed.append(email)

    logger.info("Bulk email: %d sent, %d failed", success, len(failed))
    return {'success': success, 'failed': failed}
