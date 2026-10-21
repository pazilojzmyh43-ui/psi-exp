from django.contrib import admin

from .models import Cart, CartItem, Category, MaterialVideo, News, Order, OrderItem, Profile, Service

admin.site.register(Category)
admin.site.register(Service)
admin.site.register(News)
admin.site.register(Profile)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(MaterialVideo)
