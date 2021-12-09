from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext as _
from app import models


@admin.register(models.User)
class UserAdmin(BaseUserAdmin):
    ordering = ['id']
    list_display = ['email', 'name', 'company', 'position']
    fieldsets = (
        (None, {'fields': ('email', 'password', 'type',)}),
        (_('Personal Info'), {'fields': ('name', 'company', 'position',)}),
        (
            _('Permissions'),
            {'fields': ('is_active', 'is_staff', 'is_superuser')}
        ),
        (_('Important dates'), {'fields': ('last_login',)})
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')
        }),
    )


@admin.register(models.Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['city', 'street', 'house', 'structure', 'building', 'apartment', 'phone']


@admin.register(models.Shop)
class ShopAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    pass


@admin.register(models.ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Parameter)
class ParameterAdmin(admin.ModelAdmin):
    pass


@admin.register(models.ProductParameter)
class ProductParameterAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    pass


@admin.register(models.OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    pass
