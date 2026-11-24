import uuid

from django.db import transaction
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.emails import send_password_reset_email
from accounts.models import User
from schools.search import filter_search

from .models import Parent, StudentGuardian
from .serializers import ParentSerializer, StudentGuardianSerializer


class ParentViewSet(viewsets.ModelViewSet):
    serializer_class = ParentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Parent.objects.prefetch_related('studentguardian_set__student').order_by('last_name', 'first_name')
        if not user.is_superuser:
            # Filtre sur la fiche elle-même plutôt que sur l'école des enfants : c'est
            # direct, et un parent sans enfant reste visible de son établissement.
            qs = qs.filter(school_id=user.school_id)
        # On cherche aussi sur le nom des enfants : « le parent de Kone Ama » est
        # souvent la seule chose que le directeur a en tête.
        return filter_search(
            qs,
            self.request.query_params.get('search'),
            ['first_name', 'last_name', 'phone_number', 'email'],
            related_fields=['students__first_name', 'students__last_name'],
        )

    def perform_create(self, serializer):
        serializer.save(school_id=self.request.user.school_id)

    @action(detail=True, methods=['post'], url_path='activer-portail')
    def activer_portal(self, request, pk=None):
        parent = self.get_object()
        if not request.user.school_id or request.user.is_superuser:
            return Response({'detail': "Seul le personnel de l'école peut activer un accès parent."}, status=status.HTTP_403_FORBIDDEN)
        email = (parent.email or '').strip()
        if not parent.is_active:
            return Response({'email': 'Cette fiche parent est désactivée.'}, status=status.HTTP_400_BAD_REQUEST)
        if not email:
            return Response({'email': "Ajoutez d'abord une adresse email sur la fiche parent."}, status=status.HTTP_400_BAD_REQUEST)
        if not parent.students.filter(is_active=True).exists():
            return Response({'detail': "Rattachez au moins un élève à cette fiche parent avant d'activer le portail."}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email__iexact=email).exclude(parent_profile=parent).exists():
            return Response({'email': 'Cette adresse email est déjà associée à un autre compte.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            account = User.objects.filter(parent_profile=parent).first()
            created = account is None
            if created:
                account = User.objects.create(
                    username=f'parent-{parent.school_id}-{uuid.uuid4().hex}',
                    email=email,
                    first_name=parent.first_name,
                    last_name=parent.last_name,
                    school=parent.school,
                    account_type=User.AccountType.PARENT,
                    parent_profile=parent,
                    is_active=True,
                )
                account.set_unusable_password()
                account.save(update_fields=['password'])
            else:
                account.email = email
                account.first_name = parent.first_name
                account.last_name = parent.last_name
                account.is_active = True
                account.save(update_fields=['email', 'first_name', 'last_name', 'is_active'])

        email_sent = send_password_reset_email(account)
        message = (
            "Compte parent créé. Un lien pour choisir le mot de passe a été envoyé par email."
            if created and email_sent
            else "Compte parent créé, mais l'email n'a pas pu être envoyé. Vérifiez la configuration email et renvoyez l'invitation."
            if created
            else "Le compte existe déjà ; un nouveau lien de mot de passe a été demandé."
        )
        return Response(
            {'detail': message, 'created': created, 'email_sent': email_sent},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class StudentGuardianViewSet(viewsets.ModelViewSet):
    serializer_class = StudentGuardianSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = StudentGuardian.objects.select_related('student', 'parent')
        if user.is_superuser:
            return qs
        return qs.filter(student__school_id=user.school_id)

    def _check_schools(self, student, parent):
        """L'élève et le parent doivent appartenir à l'école de l'utilisateur. Vérifier
        aussi le parent empêche de rattacher un enfant à la fiche d'un autre
        établissement — ce qui exposerait ses coordonnées."""
        user = self.request.user
        if user.is_superuser:
            return
        if student.school_id != user.school_id:
            raise serializers.ValidationError({'student': "Cet élève n'appartient pas à votre établissement."})
        if parent.school_id != user.school_id:
            raise serializers.ValidationError({'parent': "Ce parent n'appartient pas à votre établissement."})

    def perform_create(self, serializer):
        self._check_schools(serializer.validated_data['student'], serializer.validated_data['parent'])
        serializer.save()

    def perform_update(self, serializer):
        student = serializer.validated_data.get('student', serializer.instance.student)
        parent = serializer.validated_data.get('parent', serializer.instance.parent)
        self._check_schools(student, parent)
        serializer.save()
