from django.utils import timezone
from rest_framework import serializers

from academics.models import Inscription

from .models import Incident


class IncidentSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    classroom_name = serializers.CharField(source='classroom.name', read_only=True)
    annee_label = serializers.CharField(source='annee.label', read_only=True)
    category_label = serializers.CharField(source='get_category_display', read_only=True)
    severity_label = serializers.CharField(source='get_severity_display', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    reporter_name = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = [
            'id', 'school', 'annee', 'annee_label', 'classroom', 'classroom_name',
            'student', 'student_name', 'date', 'category', 'category_label',
            'severity', 'severity_label', 'description', 'action_taken', 'status',
            'status_label', 'resolution', 'reporter_name', 'resolved_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'school', 'annee', 'annee_label', 'classroom_name', 'student_name',
            'category_label', 'severity_label', 'status_label', 'reporter_name',
            'resolved_at', 'created_at', 'updated_at',
        ]

    def get_student_name(self, obj):
        return f'{obj.student.last_name} {obj.student.first_name}'

    def get_reporter_name(self, obj):
        if not obj.reported_by:
            return ''
        return obj.reported_by.get_full_name() or obj.reported_by.username

    def validate(self, attrs):
        user = self.context['request'].user
        school_id = user.school_id
        student = attrs.get('student', getattr(self.instance, 'student', None))
        classroom = attrs.get('classroom', getattr(self.instance, 'classroom', None))
        if not school_id:
            raise serializers.ValidationError('Ce compte doit être rattaché à une école.')
        if student and student.school_id != school_id:
            raise serializers.ValidationError({'student': "Cet élève n'appartient pas à votre école."})
        if classroom and classroom.school_id != school_id:
            raise serializers.ValidationError({'classroom': "Cette classe n'appartient pas à votre école."})
        if student and classroom:
            annee = classroom.annee
            if not student.inscriptions.filter(
                annee=annee,
                classe=classroom,
                statut=Inscription.Statut.INSCRIT,
            ).exists():
                raise serializers.ValidationError({'student': "Cet élève n'est pas inscrit dans cette classe."})
        return attrs

    def create(self, validated_data):
        classroom = validated_data['classroom']
        return super().create({
            **validated_data,
            'school_id': self.context['request'].user.school_id,
            'annee': classroom.annee,
            'reported_by': self.context['request'].user,
        })

    def update(self, instance, validated_data):
        classroom = validated_data.get('classroom', instance.classroom)
        validated_data['annee'] = classroom.annee
        status_value = validated_data.get('status', instance.status)
        if status_value == Incident.Status.RESOLVED and instance.status != Incident.Status.RESOLVED:
            validated_data['resolved_at'] = timezone.now()
        elif status_value == Incident.Status.OPEN and instance.status == Incident.Status.RESOLVED:
            validated_data['resolved_at'] = None
            validated_data['resolution'] = ''
        return super().update(instance, validated_data)
