from decimal import Decimal

from rest_framework import serializers

from academics.models import Inscription

from .models import FeeInvoice, FeePayment


class FeePaymentSerializer(serializers.ModelSerializer):
    method_label = serializers.CharField(source='get_method_display', read_only=True)

    class Meta:
        model = FeePayment
        fields = [
            'id', 'amount', 'method', 'method_label', 'reference',
            'paid_at', 'note', 'created_at',
        ]
        read_only_fields = ['id', 'method_label', 'created_at']

    def validate_amount(self, value):
        invoice = self.context['invoice']
        paid = sum((payment.amount for payment in invoice.payments.all()), Decimal('0.00'))
        balance = invoice.amount - paid
        if value <= 0:
            raise serializers.ValidationError('Le paiement doit être supérieur à zéro.')
        if value > balance:
            raise serializers.ValidationError(f'Le solde restant est de {balance}.')
        return value


class FeeInvoiceSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    classroom_name = serializers.CharField(source='classroom.name', read_only=True)
    annee_label = serializers.CharField(source='annee.label', read_only=True)
    paid_amount = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    financial_status = serializers.SerializerMethodField()
    payments = FeePaymentSerializer(many=True, read_only=True)

    class Meta:
        model = FeeInvoice
        fields = [
            'id', 'school', 'annee', 'annee_label', 'classroom', 'classroom_name',
            'student', 'student_name', 'title', 'amount', 'due_date', 'status',
            'paid_amount', 'balance', 'financial_status', 'payments', 'created_at',
        ]
        read_only_fields = [
            'id', 'school', 'annee', 'annee_label', 'classroom_name',
            'student_name', 'paid_amount', 'balance', 'financial_status',
            'payments', 'created_at',
        ]

    def get_student_name(self, obj):
        return f'{obj.student.last_name} {obj.student.first_name}'

    def _paid(self, obj):
        return sum((payment.amount for payment in obj.payments.all()), Decimal('0.00'))

    def get_paid_amount(self, obj):
        return str(self._paid(obj))

    def get_balance(self, obj):
        return str(max(obj.amount - self._paid(obj), Decimal('0.00')))

    def get_financial_status(self, obj):
        if obj.status == FeeInvoice.Status.CANCELLED:
            return 'CANCELLED'
        paid = self._paid(obj)
        if paid >= obj.amount:
            return 'PAID'
        return 'PARTIAL' if paid else 'UNPAID'

    def validate(self, attrs):
        school_id = self.context['request'].user.school_id
        classroom = attrs.get('classroom', getattr(self.instance, 'classroom', None))
        student = attrs.get('student', getattr(self.instance, 'student', None))
        if not school_id:
            raise serializers.ValidationError("Ce compte doit être rattaché à une école.")
        if classroom and classroom.school_id != school_id:
            raise serializers.ValidationError({'classroom': "Cette classe n'appartient pas à votre école."})
        if student and student.school_id != school_id:
            raise serializers.ValidationError({'student': "Cet élève n'appartient pas à votre école."})
        if classroom and student and not student.inscriptions.filter(
            annee=classroom.annee,
            classe=classroom,
            statut=Inscription.Statut.INSCRIT,
        ).exists():
            raise serializers.ValidationError({'student': "Cet élève n'est pas inscrit dans cette classe."})
        if attrs.get('status') == FeeInvoice.Status.CANCELLED and self.instance:
            paid = sum((payment.amount for payment in self.instance.payments.all()), Decimal('0.00'))
            if paid:
                raise serializers.ValidationError({'status': 'Une facture avec des paiements ne peut pas être annulée.'})
        if self.instance and 'amount' in attrs:
            paid = sum((payment.amount for payment in self.instance.payments.all()), Decimal('0.00'))
            if attrs['amount'] < paid:
                raise serializers.ValidationError({'amount': f'Le montant ne peut pas être inférieur aux paiements déjà enregistrés ({paid}).'})
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


class FeeBatchSerializer(serializers.Serializer):
    classroom = serializers.IntegerField(min_value=1)
    title = serializers.CharField(max_length=120)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    due_date = serializers.DateField()
