from django.urls import path
from .views import SocialLoginView

app_name = 'accounts'

urlpatterns = [
    path('oauth/login/', SocialLoginView.as_view()),
]
