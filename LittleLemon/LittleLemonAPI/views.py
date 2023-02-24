from rest_framework import generics
from .serializers import MenuItemSerializer,UserSerializer,UserOrderSerializer,UserCartSerializer
from .models import MenuItem,Cart,Order,OrderItem
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser,IsAuthenticated,AllowAny
from django.contrib.auth.models import User,Group
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from decimal import Decimal

class MenuItemsView(generics.ListAPIView, generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ['price']
    search_fields = ['title']
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return[IsAdminUser()]
        return[AllowAny()]

class SingleItemVIew(generics.ListAPIView, generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    def get_permissions(self):
        if self.request.method == 'POST' or self.request.method == 'DELETE' \
            or self.request.method == 'PUT' or self.request.method == 'PATCH':
            return [IsAdminUser()]
        return[AllowAny()]

class ManagerUserView(generics.ListCreateAPIView):
    serializer_class= UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        manager_group = Group.objects.get(name='manager')
        queryset = User.objects.filter(groups = manager_group)
        return queryset
    
    def perform_create(self, serializer):
        manager_group = Group.objects.get(name='manager')
        user = serializer.save()
        user.groups.add(manager_group)

class ManagerSingleUserView(generics.RetrieveDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        manager_group = Group.objects.get(name = 'manager')
        queryset = User.objects.filter(groups = manager_group)
        return queryset
    
class DeliveryCrewManagement(generics.ListCreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        deliveryGroup = Group.objects.get(name='delivery crew')
        queryset = User.objects.filter(name = deliveryGroup)
        return queryset
    def performCreate(self, serializer):
        deliveryGroup = Group.objects.get(name='delivery crew')
        user = serializer.save()
        user.groups.add(deliveryGroup)

class DeliveryCrewManagementSingleView(generics.RetrieveDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        deliveryGroup = Group.objects.get(name='delivery crew')
        queryset = User.objects.filter(name=deliveryGroup)
        return queryset

class CustomerCart(generics.ListCreateAPIView):
    serializer_class = UserCartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Cart.objects.filter(user = user)

    def perform_create(self, serializer):
        menuitem = self.request.data.get('menuitem')
        quantity = self.request.data.get('quantity')
        uint_price = self.request.data.get(pk=menuitem).price
        quantity = int(quantity)
        price = quantity * uint_price
        serializer.save(user=self.request.user, price=price)
    
    def delete(self,request):
        user = self.request.user
        Cart.objects.filter(user=user).delete()
        return Response(status=204)

class OrderView(generics.ListCreateAPIView):
    serializer_class = UserOrderSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def perform_create(self, serializer):
        cartItems = Cart.objects.filter(user=self.request.user)
        total = self.calculateTotal(cartItems)
        order = serializer.save(user=self.request.user, total=total)
        for cartItem in cartItems:
            OrderItem.objects.create(menuitem=cartItem.menuitem, quantity=cartItem.quantity,
            unit_price = cartItem.unit_price, price=cartItem.price, order=order)

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='manager').exists():
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def calculateTotal(self, cartItems):
        total = Decimal(0)
        for item in cartItems:
            total += item.price
        return total

class SingleOrderView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='manager').exists():
            return Order.objects.all()
        return Order.objects.filter(user=user)