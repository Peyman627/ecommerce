from django.views import generic
from django.shortcuts import render
from django.urls import reverse

from rest_framework import generics

from products.serializers import ProductSerializer, CategorySerializer
from .models import Category, Product


class ProductListAPIView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class ProductDetailAPIView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


def home_view(request):
    """ simple view to give access to the categories """
    context = {
        'category_list': reverse('products:category_list'),
    }
    return render(request, 'products/home.html', context)


class CategoryListView(generic.ListView):
    queryset = Category.objects.all()
    template_name = 'products/category_list.html'
    context_object_name = 'categories'


class ProductListView(generic.ListView):
    template_name = 'products/product_list.html'
    context_object_name = 'products'

    def get_queryset(self):
        return Product.objects.filter(category__name=self.kwargs['category'])


class ProductDetailView(generic.DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    pk_url_kwarg = 'product_id'
