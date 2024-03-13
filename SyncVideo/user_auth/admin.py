from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from SyncVideo.user_auth.models import AppUser


class AppUserAdmin(UserAdmin):
    model = AppUser
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    list_display = ('username', 'email', 'is_staff')
    list_filter = ('is_staff', 'is_superuser')
    search_fields = ('username', 'email')
    ordering = ('username',)
    filter_horizontal = ('groups',)


admin.site.register(AppUser, AppUserAdmin)