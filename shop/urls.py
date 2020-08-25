from . import views
from django.urls import path

app_name='shop'
urlpatterns=[
    path('',views.index,name='index'),
    path('checkout/',views.checkout,name='checkout'),
    path('product/<int:id>/',views.product,name='product'),
    path('store/',views.store,name='store'),
    path('to_bank/<int:order_id>/',views.to_bank,name='to_bank'),
    path('callback/',views.callback,name='callback'),
    path('profile/',views.profile,name='profile'),
    path('orders/',views.orders,name='orders'),
    path('searched_products/',views.search,name='search'),
    path('order_detail/<int:order_id>/',views.order_detail,name='order_detail')
]