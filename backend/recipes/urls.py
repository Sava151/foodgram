from django.urls import path

from .views import ShortCodeRedirect

urlpatterns = [
    path('s/<str:short_code>/', ShortCodeRedirect.as_view()),
]
