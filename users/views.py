import logging
import random
import string

import requests
from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from config import settings
from users.models import User

logger = logging.getLogger(__name__)


class SendConfirmCodeView(APIView):
    def post(self, request):
        phone_number = request.data.get('phone_number')

        if not phone_number:
            return Response({'error': 'Номер телефона обязателен'}, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"Попытка создать пользователя с номером: {phone_number}")

        confirm_code = ''.join(random.choices(string.digits, k=4))

        try:
            user, created = User.objects.get_or_create(phone_number=phone_number)
            logger.info(f"Пользователь: {user.phone_number}, Создан: {created}")
        except Exception as e:
            logger.error(f"Ошибка при создании пользователя: {e}")
            return Response({"error": "Ошибка при создании пользователя"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        user.confirm_code = confirm_code
        user.save()
        print(f"Пользователь: {user.phone_number}, Код: {user.confirm_code}")

        sms_url = 'https://sms.ru/sms/send'
        params = {
            'api_id': settings.SMS_API,
            'to': phone_number,
            'msg': f"Ваш код подтверждения: {confirm_code}",
            'json': 1
        }
        response = requests.get(sms_url, params=params)

        if response.status_code == 200 and response.json().get('status') == 'OK':
            return Response({'message': 'Код отправлен'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Ошибка при отправке SMS'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConfirmCodeView(APIView):
    def post(self, request):
        phone_number = request.data.get('phone_number')
        confirm_code = request.data.get('confirm_code')

        if not phone_number or not confirm_code:
            return Response({'error': 'Номер телефона и код подтверждения обязательны!'},
                            status=status.HTTP_400_BAD_REQUEST)
        logger.info(f"Поиск пользователя с номером: {phone_number}")
        try:
            user = User.objects.get(phone_number=phone_number)
            logger.info(f"Пользователь найден: {user.phone_number}, Код: {user.confirm_code}")
        except User.DoesNotExist:
            logger.error(f"Пользователь с номером {phone_number} не найден")
            return Response({"error": "Пользователь с таким номером телефона не найден"},
                            status=status.HTTP_404_NOT_FOUND)


        # user = get_object_or_404(User, phone_number=phone_number)
        if user.confirm_code == confirm_code:
            user.is_active = True
            user.save()
            return Response({'message': 'Код подтвержден'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Неверный код подтверждения'}, status=status.HTTP_400_BAD_REQUEST)
