
from django.contrib import admin
from .models import User


class UserAdmin(admin.ModelAdmin):
    list_display=('username', 'first_name' , 'last_name','phone_number', 'role')
    
admin.site.register(User, UserAdmin)