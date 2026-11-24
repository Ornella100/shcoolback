from rest_framework import serializers

from accounts.models import User
from .models import Parent, StudentGuardian


class StudentGuardianSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentGuardian
        fields = ['id', 'student', 'parent', 'relationship', 'is_primary_contact', 'student_name']

    def get_student_name(self, obj):
        return str(obj.student)


class ParentSerializer(serializers.ModelSerializer):
    students = StudentGuardianSerializer(source='studentguardian_set', many=True, read_only=True)
    has_portal_account = serializers.SerializerMethodField()

    class Meta:
        model = Parent
        fields = [
            'id', 'school', 'first_name', 'last_name', 'phone_number', 'whatsapp_number',
            'email', 'preferred_channel', 'is_active', 'students', 'has_portal_account', 'created_at',
        ]
        read_only_fields = ['id', 'school', 'created_at']

    def get_has_portal_account(self, obj):
        return User.objects.filter(parent_profile=obj).exists()
