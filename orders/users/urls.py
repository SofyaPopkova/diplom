from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

app_name = 'users'
router = SimpleRouter()

router.register(r'contact', views.ContactViewSet, basename='contact')

urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create'),
    path('token/', views.CreateTokenView.as_view(), name='token'),
    path('me/', views.ManageUserView.as_view(), name='me'),
]
urlpatterns += router.urls
