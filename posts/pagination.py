from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class ListPagination(PageNumberPagination):
    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        self.page_size = self.get_page_size(request)
        self.count = len(queryset)
        self.page = (self.request.query_params.get(self.page_query_parameter, 1))

        if not isinstance(self.page, int):
            self.page = 1

        self.start = (self.page - 1) * self.page_size
        self.stop = self.page * self.page_size
        return queryset[self.start:self.stop]

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.count,
            'results': data,
        })
