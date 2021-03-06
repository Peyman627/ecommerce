import jwt

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import DjangoUnicodeDecodeError, smart_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import authenticate

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import permissions

from .serializers import RegisterSerializer, EmailVerificationSerializer, LoginSerializer, PasswordResetSerializer, SetNewPasswordSerializer, LogoutSerializer, PhoneTokenCreateSerializer, PhoneTokenValidateSerializer
from .models import User, PhoneToken
from .utils import Util


class RegisterView(generics.GenericAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny, )

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user = User.objects.get(email=serializer.data['email'])
        token = RefreshToken.for_user(user).access_token

        current_site = get_current_site(request).domain
        relative_link = reverse('users:email_verify')
        absolute_url = f'http://{current_site}{relative_link}?token={token}'

        email_body = f'Hi {user.username}. Please use the link below to verify your email\n{absolute_url}'
        email_data = {
            'subject': 'Verify your email',
            'body': email_body,
            'to': user.email
        }

        Util.send_email(email_data)

        return Response(
            {
                'success':
                'User created, you can now activate your account using the email we sent you'
            },
            status=status.HTTP_201_CREATED)


class EmailVerifyView(generics.GenericAPIView):
    serializer_class = EmailVerificationSerializer
    permission_classes = (permissions.AllowAny, )

    def get(self, request):
        token = request.query_params.get('token')
        try:
            payload = jwt.decode(token,
                                 settings.SECRET_KEY,
                                 algorithms=['HS256'])

            user = User.objects.get(pk=payload['user_id'])
            if not user.is_verified:
                user.is_verified = True
                user.save()

            return Response({'success': "Successfully activated"},
                            status=status.HTTP_200_OK)

        except jwt.ExpiredSignatureError:
            return Response({'error': 'Activation expired'},
                            status=status.HTTP_400_BAD_REQUEST)

        except jwt.exceptions.DecodeError:
            return Response({'error': 'Invalid token'},
                            status=status.HTTP_400_BAD_REQUEST)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = (permissions.AllowAny, )

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class PasswordResetView(generics.GenericAPIView):
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(
            {'success': 'We have sent you a link to reset your password'},
            status=status.HTTP_200_OK)


class PasswordTokenCheckView(generics.GenericAPIView):
    def get(self, request, uidb64, token):
        try:
            user_id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=user_id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response(
                    {'error': 'Token is not valid, please request a new one'},
                    status=status.HTTP_401_UNAUTHORIZED)

            return Response(
                {
                    'success': 'Credentials valid',
                    'uidb64': uidb64,
                    'token': token
                },
                status=status.HTTP_200_OK)

        except DjangoUnicodeDecodeError:
            return Response(
                {'error': 'Token is not valid, please request a new one'},
                status=status.HTTP_401_UNAUTHORIZED)


class SetNewPasswordView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response({'success': 'Password reset complete'},
                        status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class GenerateOTP(generics.CreateAPIView):
    queryset = PhoneToken.objects.all()
    serializer_class = PhoneTokenCreateSerializer
    permission_classes = (permissions.AllowAny, )

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        if serializer.is_valid():
            token = PhoneToken.create_otp_for_number(
                number=request.data.get('phone'))

            if token:
                phone_token = self.serializer_class(
                    token, context={'request': request})
                data = phone_token.data

                if getattr(settings, 'PHONE_LOGIN_DEBUG', False):
                    data['debug_mode_token'] = token.otp

                return Response(data)
            return Response(
                {
                    'reason':
                    "you can not have more than {n} attempts per day, please try again tomorrow"
                    .format(n=getattr(settings, 'PHONE_LOGIN_ATTEMPTS', 10))
                },
                status=status.HTTP_403_FORBIDDEN)
        return Response({'reason': serializer.errors},
                        status=status.HTTP_406_NOT_ACCEPTABLE)


class ValidateOTP(generics.CreateAPIView):
    queryset = PhoneToken.objects.all()
    serializer_class = PhoneTokenValidateSerializer
    permission_classes = (permissions.AllowAny, )

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        if serializer.is_valid():
            pk = request.data.get("pk")
            otp = request.data.get("otp")
            try:
                user = authenticate(request, pk=pk, otp=otp)
                user_data = {
                    'username': user.username,
                    'tokens': user.tokens()
                }
                return Response(user_data, status=status.HTTP_200_OK)

            except ObjectDoesNotExist:
                return Response({'reason': "OTP doesn't exist"},
                                status=status.HTTP_406_NOT_ACCEPTABLE)

        return Response({'reason': serializer.errors},
                        status=status.HTTP_406_NOT_ACCEPTABLE)
