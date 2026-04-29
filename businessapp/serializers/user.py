from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


def _apply_display_name(user, name: str) -> None:
    parts = name.split(None, 1)
    user.first_name = parts[0]
    user.last_name = parts[1] if len(parts) > 1 else ''


class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, allow_blank=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'name', 'role', 'is_active', 'last_login']
        read_only_fields = ['id', 'last_login']
        extra_kwargs = {
            'email': {'required': False, 'allow_blank': True},
        }

    def validate(self, attrs):
        # required=False still allows omitting name on create unless we enforce it here.
        if self.instance is None and not (attrs.get('name') or '').strip():
            raise serializers.ValidationError({'name': 'This field is required.'})
        return attrs

    def create(self, validated_data):
        name = validated_data.pop('name', '')
        user = User(**validated_data)
        _apply_display_name(user, name)
        user.save()
        return user

    def update(self, instance, validated_data):
        name = validated_data.pop('name', serializers.empty)
        instance = super().update(instance, validated_data)
        if name is not serializers.empty:
            _apply_display_name(instance, name)
        instance.save()
        return instance


class UserMeSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, allow_blank=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'name', 'role', 'is_active']
        read_only_fields = ['id', 'role', 'is_active']
        extra_kwargs = {
            'email': {'required': False, 'allow_blank': True},
        }

    def update(self, instance, validated_data):
        name = validated_data.pop('name', None)
        instance = super().update(instance, validated_data)
        if name:
            _apply_display_name(instance, name)
        instance.save()
        return instance


class UserPasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Must match new_password.'})
        return attrs


class UserChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Must match new_password.'})
        user = self.context['request'].user
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError({'old_password': 'Wrong password.'})
        return attrs
