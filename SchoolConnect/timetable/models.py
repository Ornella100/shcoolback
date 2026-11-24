from django.db import models
from django.db.models import F, Q


class ScheduleSlot(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, 'Lundi'
        TUESDAY = 1, 'Mardi'
        WEDNESDAY = 2, 'Mercredi'
        THURSDAY = 3, 'Jeudi'
        FRIDAY = 4, 'Vendredi'
        SATURDAY = 5, 'Samedi'
        SUNDAY = 6, 'Dimanche'

    school = models.ForeignKey(
        'schools.School', on_delete=models.CASCADE, related_name='schedule_slots',
    )
    annee = models.ForeignKey(
        'academics.AnneeScolaire', on_delete=models.CASCADE, related_name='schedule_slots',
    )
    classroom = models.ForeignKey(
        'academics.Classe', on_delete=models.CASCADE, related_name='schedule_slots',
    )
    subject = models.ForeignKey(
        'results.Subject', on_delete=models.PROTECT, related_name='schedule_slots',
    )
    teacher = models.ForeignKey(
        'teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='schedule_slots',
    )
    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    teacher_name = models.CharField(max_length=120, blank=True)
    room = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['weekday', 'start_time', 'classroom__name']
        constraints = [
            models.CheckConstraint(
                condition=Q(end_time__gt=F('start_time')),
                name='schedule_end_after_start',
            ),
        ]

    def __str__(self):
        return f'{self.classroom.name} — {self.subject.name}'
