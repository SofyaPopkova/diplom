from distutils.util import strtobool
from requests import get
from rest_framework.generics import ListAPIView
from yaml import load as load_yaml, Loader
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import authentication
from rest_framework.views import APIView
from django.db.models import Q, Sum, F
from rest_framework.permissions import IsAuthenticated
from app.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter
from .serializers import CategorySerializer, ShopSerializer, ProductInfoSerializer
from .permissions import IsAdminOrReadOnly
from clients.serializers import OrderSerializer
from app.models import Order


class CategoryView(ListAPIView):
    throttle_scope = 'anon'
    permission_classes = (IsAdminOrReadOnly,)
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    throttle_scope = 'anon'
    permission_classes = (IsAdminOrReadOnly,)
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer


class ProductInfoView(APIView):
    throttle_scope = 'anon'
    permission_classes = (IsAdminOrReadOnly,)
    serializer_class = ProductInfoSerializer

    def get(self, request, *args, **kwargs):
        query = Q(shop__state=True)
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')

        if shop_id:
            query = query & Q(shop_id=shop_id)

        if category_id:
            query = query & Q(product__category_id=category_id)

        queryset = ProductInfo.objects.filter(
            query).select_related(
            'shop', 'product__category').prefetch_related(
            'product_parameters__parameter').distinct()

        serializer = ProductInfoSerializer(queryset, many=True)

        return Response(serializer.data)


class ShopUpdate(APIView):
    throttle_scope = 'uploads'
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ShopSerializer

    def post(self, request, *args, **kwargs):
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Тип пользователя должен быть "Магазин"'}, status=403)

        url = request.data.get('url')
        if url:
            validate_url = URLValidator()
            try:
                validate_url(url)
            except ValidationError as e:
                return JsonResponse({'Status': False, 'Error': str(e)})
            else:
                stream = get(url).text
                data = load_yaml(stream, Loader=Loader)
                shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
                for category in data['categories']:
                    category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                    category_object.shops.add(shop.id)
                    category_object.save()

                ProductInfo.objects.filter(shop_id=shop.id).delete()
                for item in data['goods']:
                    product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

                    product_info = ProductInfo.objects.create(product_id=product.id,
                                                              external_id=item['id'],
                                                              model=item['model'],
                                                              price=item['price'],
                                                              price_rrc=item['price_rrc'],
                                                              quantity=item['quantity'],
                                                              shop_id=shop.id)
                    for name, value in item['parameters'].items():
                        parameter_object, _ = Parameter.objects.get_or_create(name=name)
                        ProductParameter.objects.create(product_info_id=product_info.id,
                                                        parameter_id=parameter_object.id,
                                                        value=value)

                return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны необходимые аргументы'})


class ShopState(APIView):
    throttle_scope = 'user'
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ShopSerializer

    def get(self, request, *args, **kwargs):
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Тип пользователя должен быть "Магазин"'}, status=403)

        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Тип пользователя должен быть "Магазин"'}, status=403)

        state = request.data.get('state')
        if state:
            try:
                Shop.objects.filter(user_id=request.user.id).update(state=strtobool(state))
                return JsonResponse({'Status': True})
            except ValueError as error:
                return JsonResponse({'Status': False, 'Errors': str(error)})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны необходимые аргументы'})


class ShopOrders(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrderSerializer

    def get(self, request, *args, **kwargs):
        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Тип пользователя должен быть "Магазин"'}, status=403)

        order = Order.objects.filter(
            ordered_items__product_info__shop__user_id=request.user.id).exclude(state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)
