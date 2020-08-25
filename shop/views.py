from django.shortcuts import render, get_object_or_404, redirect
from cart.forms import CartAddProductForm
from django.contrib.auth.decorators import login_required
from .forms import AddressForm
from . import models
from cart.cart import Cart
from django.db.models import Q
from decimal import Decimal
from zeep import Client
from django.http import HttpResponse
 
def index(request):
    product_list = models.Product.objects.order_by('-create_time')[:10]
    return render(request, 'index.html', {'product_list': product_list})


def product(request, id):
    product_detail = get_object_or_404(models.Product, id=id)
    cart_add_product_form = CartAddProductForm()
    return render(request, 'product.html',
                  {'product_detail': product_detail, 'cart_add_product_form': cart_add_product_form})


def store(request):
    products = models.Product.objects.order_by('-create_time')
    return render(request, 'store.html', {'products': products})


def search(request):
    query = request.GET.get('q')
    queryset_list = []
    if query:
        queryset_list = models.Product.objects.filter(Q(name__icontains=query)).distinct()
    elif query == '':
        queryset_list = models.Product.objects.all()
    products = queryset_list
    return render(request, 'searched_products.html', {'products': products})
  

@login_required()
def checkout(request):
    cart = Cart(request)
    if not cart:
        return redirect('shop:store')
    if request.method != 'POST':
        form = AddressForm()
    else:
        form = AddressForm(request.POST)
        if form.is_valid():
            address = models.Address.objects.create(
                name=request.POST.get('name'),
                mobile=request.POST.get('mobile'),
                address=request.POST.get('address'),
                user=request.user
            )

            order = models.Order.objects.create(customer=request.user, address=address)
            for item in cart:
                models.OrderItem.objects.create(
                    order=order, 
                    product=item['product'],
                    product_price=item['price'],
                    product_count=item['product_count'],
                    product_cost=Decimal(item['product_count']) * Decimal(item['price'])
                )
        cart.clear()
        return redirect('shop:order_detail', order.id)
    return render(request, 'checkout.html', {'form': form})


def profile(request):
    return render(request, 'profile.html')


def orders(request):
    orders = models.Order.objects.order_by('-order_date')
    return render(request, 'orders.html', {'orders': orders})


def order_detail(request, order_id):
    order = get_object_or_404(models.Order, id=order_id)
    return render(request, 'order_detail.html', {'order': order})

MERCHANT='*******************'
client=Client('https://www.zarinpal.com/pg/services/WebGate/wsdl')
def to_bank(request,order_id):
    order=get_object_or_404(models.Order,id=order_id)
    amount=0
    order_items=models.OrderItem.objects.filter(order=order)
    for item in order_items:
        amount+=item.product_price
    callbackUrl='http://beontop.ir/callback/'
    mobile=''
    email=''
    description='Test'
    result=client.service.PaymentRequest(MERCHANT,amount,description,email,mobile,callbackUrl)
    if result.Status == 100 and len(result.Authority) == 36:
        x=[]
        for item in order_items:
            x.append(item)
        models.Invoice.objects.create(order=order,
                                      order_items=x,
                                      authority=result.Authority)
        return redirect('https://www.zarinpal.com/pg/StartPay/'+result.Authority)
    else:
        return HttpResponse('Error code' + str(result.Status))


def callback(request):
    if request.GET.get('Status')=='OK':
        authority=request.GET.get('Authority')
        invoice=get_object_or_404(models.Invoice,authority=authority)
        amount=0
        order=invoice.order
        order_items=models.OrderItem.objects.filter(order=order)
        for item in order_items:
            amount+=item.product_cost
        result=client.service.PaymentVerification(MERCHANT,authority,amount)
        if result.Status == 100:
            
            order.payed=True
            order.save()
            return render(request,'callback.html',{'invoice':invoice})
        else:
            return HttpResponse('error'+str(result.Status))
    else:
        return HttpResponse('error')


