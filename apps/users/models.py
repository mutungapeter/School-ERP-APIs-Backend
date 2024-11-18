
from django.contrib.auth.models import AbstractUser
from django.db import models
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
class AbstractBaseModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class User(AbstractBaseModel, AbstractUser):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Teacher', 'Teacher'),
        ('Principal', 'Principal'),
        ('Secretary', 'Secretary')
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Teacher')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, blank=False, null=False)
    password_reset_token = models.CharField(max_length=64, blank=True, null=True)
    token_created_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.username}"
    
    def get_jwt_tokens(self):
        refresh = RefreshToken.for_user(self)

        # Adding custom claims to the token payload
        refresh['username'] = self.username
        refresh['email'] = self.email
        refresh['role'] = self.role
        refresh['phone_number'] = self.phone_number
        refresh['first_name'] = self.first_name
        refresh['last_name'] = self.last_name

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
