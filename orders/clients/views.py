from django.db import IntegrityError
from django.http import JsonResponse
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Sum, F
from ujson import loads as load_json
from .serializers import OrderSerializer, OrderItemSerializer
from app.models import Order, OrderItem, User
from orders.tasks import send_email


class BasketView(APIView):
    """
    Класс и методы корзины пользователя
    """
    throttle_scope = 'user'
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = OrderSerializer

    def get(self, request, *args, **kwargs):
        basket = Order.objects.filter(
            user_id=request.user.id, state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        items_string = request.data.get('items')
        if items_string:
            try:
                items_dict = load_json(items_string)
            except ValueError:
                JsonResponse({'Status': False, 'Errors': 'Неверный формат'})
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
                objects_created = 0
                for order_item in items_dict:
                    order_item.update({'order': basket.id})
                    serializer = OrderItemSerializer(data=order_item)
                    if serializer.is_valid():
                        try:
                            serializer.save()
                        except IntegrityError as error:
                            return JsonResponse({'Status': False, 'Errors': f"Товар уже выбран"})
                        else:
                            objects_created += 1

                    else:
                        JsonResponse({'Status': False, 'Errors': serializer.errors})

                return JsonResponse({'Status': True, 'Message': f"Товары {objects_created} добавлены"})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны необходимые аргументы'})

    def delete(self, request, *args, **kwargs):
        items_string = request.data.get('items')
        if items_string:
            items_list = items_string.split(',')
            basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
            query = Q()
            objects_deleted = False
            for order_item_id in items_list:
                if order_item_id.isdigit():
                    query = query | Q(order_id=basket.id, id=order_item_id)
                    objects_deleted = True

            if objects_deleted:
                deleted_count = OrderItem.objects.filter(query).delete()[0]
                return JsonResponse({'Status': True, 'Удалены': deleted_count})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны необходимые аргументы'})

    def put(self, request, *args, **kwargs):
        items_string = request.data.get('items')
        if items_string:
            try:
                items_dict = load_json(items_string)
            except ValueError:
                JsonResponse({'Status': False, 'Errors': 'Неверный формат'})
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
                objects_updated = 0
                for order_item in items_dict:
                    if type(order_item['id']) == int and type(order_item['quantity']) == int:
                        objects_updated += OrderItem.objects.filter(order_id=basket.id, id=order_item['id']).update(
                            quantity=order_item['quantity'])

                return JsonResponse({'Status': True, 'Обновлены': objects_updated})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны необходимые аргументы'})


class OrderView(APIView):
    """
    Класс и методы заказов пользователя
    """
    throttle_scope = 'user'
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = OrderSerializer

    def get(self, request, *args, **kwargs):
        order = Order.objects.filter(
            user_id=request.user.id).exclude(state='basket').prefetch_related(
            'ordered_items__product_info__product__category',
            'ordered_items__product_info__product_parameters__parameter').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))).distinct()

        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if {'id', 'contact'}.issubset(request.data):
            if request.data['id'].isdigit():
                try:
                    is_updated = Order.objects.filter(
                        user_id=request.user.id, id=request.data['id']).update(
                        contact_id=request.data['contact'],
                        state='new')
                except IntegrityError as error:
                    print(error)
                    return JsonResponse({'Status': False, 'Errors': 'Неправильно указаны аргументы'})
                else:
                    if is_updated:
                        print(f'Отправка уведомления при изменении статуса заказа.')
                        user = User.objects.get(id=request.user.id)
                        title = 'Уведомление об изменении статуса заказа'
                        message = 'Заказ оформлен.'
                        email = user.email
                        send_email.apply_async((title, message, email), countdown=5 * 60)

                        return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны необходимые аргументы'})
