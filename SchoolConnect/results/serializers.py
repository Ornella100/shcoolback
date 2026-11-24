from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from academics.models import Classe

from .models import Assessment, StudentScore, Subject


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'school', 'name', 'coefficient', 'created_at']
        read_only_fields = ['id', 'school', 'created_at']

    def validate_coefficient(self, value):
        if value <= 0:
            raise ValidationError('Le coefficient doit être supérieur à zéro.')
        return value


class AssessmentSerializer(serializers.ModelSerializer):
    classroom_name = serializers.CharField(source='classroom.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    annee_label = serializers.CharField(source='annee.label', read_only=True)
    scores_count = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = [
            'id', 'school', 'annee', 'annee_label', 'classroom', 'classroom_name',
            'subject', 'subject_name', 'title', 'date', 'max_score', 'coefficient',
            'scores_count', 'created_at',
        ]
        read_only_fields = [
            'id', 'school', 'annee', 'annee_label', 'classroom_name',
            'subject_name', 'scores_count', 'created_at',
        ]

    def get_scores_count(self, obj):
        return obj.scores.filter(score__isnull=False).count()

    def validate(self, attrs):
        request = self.context['request']
        school_id = request.user.school_id
        classroom = attrs.get('classroom', getattr(self.instance, 'classroom', None))
        subject = attrs.get('subject', getattr(self.instance, 'subject', None))
        if not school_id:
            raise serializers.ValidationError('Ce compte doit être rattaché à une école.')
        if classroom and classroom.school_id != school_id:
            raise serializers.ValidationError({'classroom': "Cette classe n'appartient pas à votre école."})
        if subject and subject.school_id != school_id:
            raise serializers.ValidationError({'subject': "Cette matière n'appartient pas à votre école."})
        return attrs

    def create(self, validated_data):
        classroom = validated_data['classroom']
        return super().create({
            **validated_data,
            'school_id': self.context['request'].user.school_id,
            'annee': classroom.annee,
        })

    def update(self, instance, validated_data):
        classroom = validated_data.get('classroom', instance.classroom)
        validated_data['annee'] = classroom.annee
        return super().update(instance, validated_data)


class StudentScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentScore
        fields = ['id', 'assessment', 'student', 'score', 'appreciation', 'updated_at']
        read_only_fields = ['id', 'assessment', 'updated_at']

    def validate_score(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError('La note ne peut pas être négative.')
        return value

    def validate(self, attrs):
        assessment = self.context['assessment']
        student = attrs['student']
        if student.school_id != assessment.school_id or not student.is_active:
            raise serializers.ValidationError({'student': "Cet élève n'appartient pas à votre école."})
        enrolled = student.inscriptions.filter(
            annee=assessment.annee,
            classe=assessment.classroom,
            statut='INSCRIT',
        ).exists()
        if not enrolled:
            raise serializers.ValidationError({'student': "Cet élève n'est pas inscrit dans cette classe pour cette année."})
        value = attrs.get('score')
        if value is not None and value > assessment.max_score:
            raise serializers.ValidationError({'score': f'La note maximale est {assessment.max_score}.'})
        return attrs
