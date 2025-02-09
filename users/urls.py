from django.urls import path

from users.apps import UsersConfig
from users.views import SendConfirmCodeView, ConfirmCodeView

app_name = UsersConfig.name

urlpatterns = [
    path('send-code/', SendConfirmCodeView.as_view(), name='send_code'),
    path('confirm-code/', ConfirmCodeView.as_view(), name='confirm_code'),
]