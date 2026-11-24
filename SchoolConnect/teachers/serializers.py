from rest_framework import serializers

from results.models import Subject

from .models import Teacher


class TeacherSerializer(serializers.ModelSerializer):
    subject_names = serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = [
            'id', 'school', 'first_name', 'last_name', 'phone_number', 'email',
            'specialty', 'subjects', 'subject_names', 'hire_date', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'school', 'subject_names', 'created_at', 'updated_at']

    def get_subject_names(self, obj):
        return [subject.name for subject in obj.subjects.all()]

    def validate_subjects(self, subjects):
        school_id = self.context['request'].user.school_id
        if any(subject.school_id != school_id for subject in subjects):
            raise serializers.ValidationError('Toutes les matières doivent appartenir à votre école.')
        return subjects

    def validate(self, attrs):
        if not self.context['request'].user.school_id:
            raise serializers.ValidationError('Ce compte doit être rattaché à une école.')
        return attrs

    def create(self, validated_data):
        subjects = validated_data.pop('subjects', [])
        teacher = Teacher.objects.create(
            school_id=self.context['request'].user.school_id,
            **validated_data,
        )
        teacher.subjects.set(subjects)
        return teacher
