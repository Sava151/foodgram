from django.urls import path

from .views import ShortCodeRedirect

urlpatterns = [
    path('<str:short_code>/', ShortCodeRedirect.as_view()),
]
