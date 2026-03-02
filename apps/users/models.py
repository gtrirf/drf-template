import uuid
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.utils import timezone

class UserRole(models.TextChoices):
    GUEST = 'guest', 'Guest'
    USER = 'user', 'User'
    ADMIN = 'admin', 'Admin'
    SUPERADMIN = 'superadmin', 'Super Admin'

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        
        email = self.normalize_email(email)
        
        if 'username' not in extra_fields or not extra_fields['username']:
            extra_fields['username'] = f"user_{uuid.uuid4().hex[:10]}" 
            
        extra_fields.setdefault('role', UserRole.GUEST)
        
        user = self.model(
            email=email,
            **extra_fields
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True) 
        extra_fields.setdefault('role', UserRole.SUPERADMIN)
        return self.create_user(email, password=password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email        = models.EmailField(unique=True) 
    username     = models.CharField(max_length=255, unique=True, blank=True) 
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    is_active    = models.BooleanField(default=False)
    is_staff     = models.BooleanField(default=False)
    date_joined  = models.DateTimeField(default=timezone.now)
    role         = models.CharField(choices=UserRole.choices, max_length=50, default=UserRole.GUEST)
    first_name   = models.CharField(max_length=150, blank=True, null=True)
    last_name    = models.CharField(max_length=150, blank=True, null=True)
    avatar       = models.ImageField(upload_to='users/avatars', default='users/avatars/default_user_img.png')
    updated_at   = models.DateTimeField(auto_now=True)
    
    objects = UserManager()

    USERNAME_FIELD = 'email' 

    REQUIRED_FIELDS = [] 

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['role']), 
            models.Index(fields=['phone_number']),
            models.Index(fields=['email']), 
        ]

    def __str__(self):
        return self.email 
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_short_name(self):
        return self.first_name if self.first_name else self.username
    
    @property
    def is_guest(self):
        return self.role == UserRole.GUEST
    
    @property
    def is_user(self):
        return self.role == UserRole.USER

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def is_superadmin(self):
        return self.role == UserRole.SUPERADMIN