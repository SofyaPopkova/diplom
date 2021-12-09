from rest_framework import generics, authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.settings import api_settings
from rest_framework.viewsets import ModelViewSet
from .serializers import UserSerializer, AuthTokenSerializer, ContactSerializer
from app.models import Contact


class CreateUserView(generics.CreateAPIView):
    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class ContactViewSet(ModelViewSet):
    throttle_scope = 'user'
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ContactSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            queryset = Contact.objects.all()
        else:
            queryset = Contact.objects.filter(user=self.request.user.id)
        return queryset
