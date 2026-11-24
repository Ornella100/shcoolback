from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from .models import Assignment, AssignmentSubmission


class AssignmentSerializer(serializers.ModelSerializer):
    classroom_name = serializers.CharField(source='classroom.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True, default='')
    annee_label = serializers.CharField(source='annee.label', read_only=True)
    submission_count = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            'id', 'school', 'annee', 'annee_label', 'classroom', 'classroom_name',
            'subject', 'subject_name', 'title', 'instructions', 'assigned_date',
            'due_date', 'max_score', 'submission_count', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'school', 'annee', 'annee_label', 'classroom_name', 'subject_name',
            'submission_count', 'created_at', 'updated_at',
        ]

    def get_submission_count(self, obj):
        return obj.submissions.exclude(status=AssignmentSubmission.Status.PENDING).count()

    def validate(self, attrs):
        school_id = self.context['request'].user.school_id
        classroom = attrs.get('classroom', getattr(self.instance, 'classroom', None))
        subject = attrs.get('subject', getattr(self.instance, 'subject', None))
        assigned_date = attrs.get('assigned_date', getattr(self.instance, 'assigned_date', None))
        due_date = attrs.get('due_date', getattr(self.instance, 'due_date', None))
        if not school_id:
            raise serializers.ValidationError('Ce compte doit être rattaché à une école.')
        if classroom and classroom.school_id != school_id:
            raise serializers.ValidationError({'classroom': "Cette classe n'appartient pas à votre école."})
        if subject and subject.school_id != school_id:
            raise serializers.ValidationError({'subject': "Cette matière n'appartient pas à votre école."})
        if assigned_date and due_date and due_date < assigned_date:
            raise serializers.ValidationError({'due_date': "L'échéance doit être le jour de publication ou après."})
        max_score = attrs.get('max_score', getattr(self.instance, 'max_score', None))
        if max_score is not None and max_score <= Decimal('0'):
            raise serializers.ValidationError({'max_score': 'Le barème doit être supérieur à zéro.'})
        return attrs

    def create(self, validated_data):
        classroom = validated_data['classroom']
        return super().create({
            **validated_data,
            'school_id': self.context['request'].user.school_id,
            'annee': classroom.annee,
            'created_by': self.context['request'].user,
        })

    def update(self, instance, validated_data):
        classroom = validated_data.get('classroom', instance.classroom)
        validated_data['annee'] = classroom.annee
        return super().update(instance, validated_data)


class AssignmentSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentSubmission
        fields = ['id', 'assignment', 'student', 'status', 'submitted_at', 'comment', 'score', 'updated_at']
        read_only_fields = ['id', 'assignment', 'submitted_at', 'updated_at']

    def validate(self, attrs):
        assignment = self.context['assignment']
        student = attrs['student']
        if student.school_id != assignment.school_id or not student.is_active:
            raise serializers.ValidationError({'student': "Cet élève n'appartient pas à votre école."})
        if not student.inscriptions.filter(
            annee=assignment.annee,
            classe=assignment.classroom,
            statut='INSCRIT',
        ).exists():
            raise serializers.ValidationError({'student': "Cet élève n'est pas inscrit dans cette classe."})
        score = attrs.get('score')
        if score is not None and score < 0:
            raise serializers.ValidationError({'score': 'La note ne peut pas être négative.'})
        if score is not None and assignment.max_score and score > assignment.max_score:
            raise serializers.ValidationError({'score': f'La note maximale est {assignment.max_score}.'})
        return attrs
