from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
from rest_framework import serializers

User = get_user_model()

class OTPVerifySerializer(serializers.Serializer):
    otp = serializers.CharField(required=True)

class UserCreateSerializer(DjoserUserCreateSerializer):
    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = ('email', 'username', 'password', 'first_name', 'last_name', 'id_no', 
                  'security_question', 'security_answer')
        
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
