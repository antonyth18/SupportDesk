from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TicketViewSet, TicketStatsView, TicketClassifyView

router = DefaultRouter()
router.register(r'tickets', TicketViewSet)

urlpatterns = [
    path('tickets/stats/', TicketStatsView.as_view(), name='ticket-stats'),
    path('tickets/classify/', TicketClassifyView.as_view(), name='ticket-classify'),
    path('', include(router.urls)),
]
