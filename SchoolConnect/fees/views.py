from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from academics.models import Classe, Eleve, Inscription

from .models import FeeInvoice
from .serializers import FeeBatchSerializer, FeeInvoiceSerializer, FeePaymentSerializer


class FeeInvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = FeeInvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _staff_required(self, request):
        return bool(request.user.school_id and request.user.account_type == 'STAFF')

    def create(self, request, *args, **kwargs):
        if not self._staff_required(request):
            return Response({'detail': 'Cette action est réservée au personnel.'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not self._staff_required(request):
            return Response({'detail': 'Cette action est réservée au personnel.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not self._staff_required(request):
            return Response({'detail': 'Cette action est réservée au personnel.'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    def get_queryset(self):
        school_id = self.request.user.school_id
        if not school_id:
            return FeeInvoice.objects.none()
        qs = FeeInvoice.objects.filter(school_id=school_id).select_related(
            'annee', 'classroom', 'student',
        ).prefetch_related('payments')
        year_id = self.request.query_params.get('annee')
        classroom_id = self.request.query_params.get('classe')
        student_id = self.request.query_params.get('eleve')
        if year_id:
            qs = qs.filter(annee_id=year_id) if year_id.isdigit() else qs.none()
        if classroom_id:
            qs = qs.filter(classroom_id=classroom_id) if classroom_id.isdigit() else qs.none()
        if student_id:
            qs = qs.filter(student_id=student_id) if student_id.isdigit() else qs.none()
        return qs

    def destroy(self, request, *args, **kwargs):
        if not self._staff_required(request):
            return Response({'detail': 'Cette action est réservée au personnel.'}, status=status.HTTP_403_FORBIDDEN)
        invoice = self.get_object()
        if invoice.payments.exists():
            return Response(
                {'detail': 'Une facture avec des paiements ne peut pas être supprimée ; annulez-la si aucun paiement n’a été encaissé.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


class FeeBatchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.school_id or request.user.account_type != 'STAFF':
            return Response({'detail': 'Cette action est réservée au personnel.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = FeeBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        classroom = get_object_or_404(
            Classe,
            id=data['classroom'],
            school_id=request.user.school_id,
        )
        students = list(Eleve.objects.filter(
            school_id=request.user.school_id,
            is_active=True,
            inscriptions__annee=classroom.annee,
            inscriptions__classe=classroom,
            inscriptions__statut=Inscription.Statut.INSCRIT,
        ).distinct())
        if not students:
            return Response({'classroom': 'Cette classe ne contient aucun élève inscrit.'}, status=status.HTTP_400_BAD_REQUEST)

        created = 0
        title = data['title'].strip()
        with transaction.atomic():
            for student in students:
                _, was_created = FeeInvoice.objects.get_or_create(
                    school_id=request.user.school_id,
                    annee=classroom.annee,
                    classroom=classroom,
                    student=student,
                    title=title,
                    defaults={
                        'amount': data['amount'],
                        'due_date': data['due_date'],
                        'created_by': request.user,
                    },
                )
                created += int(was_created)
        return Response({
            'created': created,
            'already_exists': len(students) - created,
            'classroom': classroom.name,
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class FeePaymentsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _invoice(self, request, invoice_id, lock=False):
        qs = FeeInvoice.objects.filter(
            id=invoice_id,
            school_id=request.user.school_id,
        )
        if lock:
            qs = qs.select_for_update()
        return get_object_or_404(qs.prefetch_related('payments'), status=FeeInvoice.Status.ISSUED)

    def get(self, request, invoice_id):
        invoice = self._invoice(request, invoice_id)
        return Response(FeePaymentSerializer(invoice.payments.all(), many=True).data)

    def post(self, request, invoice_id):
        if not request.user.school_id or request.user.account_type != 'STAFF':
            return Response({'detail': 'Cette action est réservée au personnel.'}, status=status.HTTP_403_FORBIDDEN)
        with transaction.atomic():
            invoice = self._invoice(request, invoice_id, lock=True)
            serializer = FeePaymentSerializer(
                data=request.data,
                context={'invoice': invoice},
            )
            serializer.is_valid(raise_exception=True)
            payment = serializer.save(invoice=invoice, recorded_by=request.user)
        return Response(
            FeePaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED,
        )
