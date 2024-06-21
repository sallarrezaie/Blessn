from django_filters import rest_framework as filters
from .models import Order


class OrderFilter(filters.FilterSet):
    status = filters.CharFilter(field_name='status', lookup_expr='in', method='filter_status')


    class Meta:
        model = Order
        fields = ['consumer', 'contributor', 'archived', 'status']

    def filter_status(self, queryset, name, value):
        statuses = value.split(',')
        return queryset.filter(**{name + '__in': statuses})
