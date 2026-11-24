from rest_framework import serializers

from .models import ScheduleSlot


class ScheduleSlotSerializer(serializers.ModelSerializer):
    classroom_name = serializers.CharField(source='classroom.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_display_name = serializers.SerializerMethodField()
    annee_label = serializers.CharField(source='annee.label', read_only=True)
    weekday_label = serializers.CharField(source='get_weekday_display', read_only=True)

    class Meta:
        model = ScheduleSlot
        fields = [
            'id', 'school', 'annee', 'annee_label', 'classroom', 'classroom_name',
            'subject', 'subject_name', 'teacher', 'teacher_display_name', 'weekday', 'weekday_label', 'start_time',
            'end_time', 'teacher_name', 'room', 'created_at',
        ]
        read_only_fields = ['id', 'school', 'annee', 'annee_label', 'classroom_name', 'subject_name', 'weekday_label', 'created_at']

    def validate(self, attrs):
        request = self.context['request']
        school_id = request.user.school_id
        classroom = attrs.get('classroom', getattr(self.instance, 'classroom', None))
        subject = attrs.get('subject', getattr(self.instance, 'subject', None))
        weekday = attrs.get('weekday', getattr(self.instance, 'weekday', None))
        start_time = attrs.get('start_time', getattr(self.instance, 'start_time', None))
        end_time = attrs.get('end_time', getattr(self.instance, 'end_time', None))

        if not school_id:
            raise serializers.ValidationError('Ce compte doit être rattaché à une école.')
        if classroom and classroom.school_id != school_id:
            raise serializers.ValidationError({'classroom': "Cette classe n'appartient pas à votre école."})
        if subject and subject.school_id != school_id:
            raise serializers.ValidationError({'subject': "Cette matière n'appartient pas à votre école."})
        teacher = attrs.get('teacher', getattr(self.instance, 'teacher', None))
        if teacher and (teacher.school_id != school_id or not teacher.is_active):
            raise serializers.ValidationError({'teacher': "Cet enseignant est inactif ou n'appartient pas à votre école."})
        if teacher:
            attrs['teacher_name'] = f'{teacher.first_name} {teacher.last_name}'
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError({'end_time': "L'heure de fin doit être après l'heure de début."})

        if classroom and weekday is not None and start_time and end_time:
            conflicting = ScheduleSlot.objects.filter(
                school_id=school_id,
                annee=classroom.annee,
                weekday=weekday,
                start_time__lt=end_time,
                end_time__gt=start_time,
            ).exclude(pk=self.instance.pk if self.instance else None)
            checks = [
                ('classroom', classroom, "La classe a déjà un cours sur ce créneau."),
            ]
            teacher = attrs.get('teacher_name', getattr(self.instance, 'teacher_name', '')).strip()
            room = attrs.get('room', getattr(self.instance, 'room', '')).strip()
            if teacher:
                checks.append(('teacher_name__iexact', teacher, "Cet enseignant a déjà un cours sur ce créneau."))
            assigned_teacher = attrs.get('teacher', getattr(self.instance, 'teacher', None))
            if assigned_teacher:
                checks.append(('teacher', assigned_teacher, "Cet enseignant a déjà un cours sur ce créneau."))
            if room:
                checks.append(('room__iexact', room, "Cette salle est déjà occupée sur ce créneau."))
            for field, value, message in checks:
                if conflicting.filter(**{field: value}).exists():
                    raise serializers.ValidationError({'start_time': message})
        return attrs

    def get_teacher_display_name(self, obj):
        return str(obj.teacher) if obj.teacher_id else obj.teacher_name
