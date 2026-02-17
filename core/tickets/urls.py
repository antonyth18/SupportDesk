from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TicketViewSet, TicketStatsView

router = DefaultRouter()
router.register(r'tickets', TicketViewSet)

urlpatterns = [
    path('tickets/stats/', TicketStatsView.as_view(), name='ticket-stats'),
    path('', include(router.urls)),
]
