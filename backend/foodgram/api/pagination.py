from rest_framework.pagination import (
    PageNumberPagination,
    LimitOffsetPagination
)


class LimitPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = 10


class LimitOffsetPaginationWithDefault(LimitOffsetPagination):
    default_limit = 6
