from django.shortcuts import get_object_or_404, redirect
from django.db.models import F

from rest_framework import generics
from rest_framework import permissions
from rest_framework.views import APIView

from .models import Cart, Entry
from products.models import Product
from .serializers import CartSerializer


class CartDetailView(generics.RetrieveAPIView):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    lookup_url_kwarg = 'cart_id'
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class AddToCartView(APIView):
    def get(self, request, product_id):
        product = get_object_or_404(Product, pk=product_id)
        entry, created = Entry.objects.get_or_create(product=product)
        entry.quantity = F('quantity') + 1
        entry.save()
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart.entries.add(entry)
        cart.save()
        return redirect('carts:cart_detail', cart_id=cart.id)
