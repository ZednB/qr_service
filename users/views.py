import logging
import random
import string

import requests
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import TemplateView

from config import settings
from users.models import User

logger = logging.getLogger(__name__)


class SendConfirmCodeView(APIView):
    def get(self, request):
        return render(request, 'survey/login.html')

    def post(self, request):
        print("Функция отправки кода вызвана")
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
        logger.info(f"Отправка SMS на номер {phone_number}")
        response = requests.get(sms_url, params=params)
        logger.info(f"Ответ от SMS-сервиса: {response.status_code} - {response.json()}")

        if response.status_code == 200 and response.json().get('status') == 'OK':
            logger.info(f"Код подтверждения отправлен на номер {phone_number}")
            redirect_url = reverse('users:confirm_code') + f"?phone_number={phone_number}"
            logger.info(f"Перенаправление на: {redirect_url}")
            return HttpResponseRedirect(redirect_url)
            # return render(request, 'confirm.html', {'phone_number': phone_number})
            # return Response({'message': 'Код отправлен'}, status=status.HTTP_200_OK)
        else:
            logger.error(f"Ошибка при отправке SMS: {response.text}")
            return Response({'error': 'Ошибка при отправке SMS'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConfirmCodeView(APIView):
    def get(self, request):
        phone_number = request.GET.get('phone_number')
        return render(request, 'survey/confirm.html', {'phone_number': phone_number})

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
            return redirect('survey')
            # return Response({'message': 'Код подтвержден'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Неверный код подтверждения'}, status=status.HTTP_400_BAD_REQUEST)


class SurveyPageView(TemplateView):
    def get_template_names(self):
        return ['survey/login.html']
