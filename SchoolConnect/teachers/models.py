from django.db import models

from schools.validators import phone_validator


class Teacher(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, related_name='teachers')
    first_name = models.CharField('prénom', max_length=100)
    last_name = models.CharField('nom', max_length=100)
    phone_number = models.CharField(
        'téléphone', max_length=20, blank=True,
        validators=[phone_validator],
    )
    email = models.EmailField(blank=True)
    specialty = models.CharField('spécialité', max_length=100, blank=True)
    subjects = models.ManyToManyField('results.Subject', blank=True, related_name='teachers')
    hire_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [models.Index(fields=['school', 'last_name', 'first_name'], name='teacher_school_name_idx')]

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
