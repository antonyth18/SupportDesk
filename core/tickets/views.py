from rest_framework import viewsets, filters, views
from rest_framework.response import Response
from django.db.models import Count, Min, Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import Ticket
from .serializers import TicketSerializer

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all().order_by('-created_at')
    serializer_class = TicketSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'priority', 'status']
    search_fields = ['title', 'description']

class TicketStatsView(views.APIView):
    def get(self, request):
        # Base aggregation
        stats = Ticket.objects.aggregate(
            total_tickets=Count('id'),
            open_tickets=Count('id', filter=Q(status=Ticket.Status.OPEN)),
            first_ticket_date=Min('created_at')
        )

        total_tickets = stats['total_tickets'] or 0
        open_tickets = stats['open_tickets'] or 0
        first_ticket_date = stats['first_ticket_date']

        # Calculate average tickets per day
        avg_tickets_per_day = 0.0
        if total_tickets > 0 and first_ticket_date:
            days_since_first = (timezone.now() - first_ticket_date).days
            # If less than a day, treat as 1 day to avoid division by zero or huge numbers
            days_since_first = max(days_since_first, 1)
            avg_tickets_per_day = total_tickets / days_since_first

        # Breakdown by priority
        priority_breakdown = {}
        priority_data = Ticket.objects.values('priority').annotate(count=Count('id'))
        for item in priority_data:
            priority_breakdown[item['priority']] = item['count']

        # Ensure all choices are present with 0 if no tickets
        for choice in Ticket.Priority.values:
            if choice not in priority_breakdown:
                priority_breakdown[choice] = 0

        # Breakdown by category
        category_breakdown = {}
        category_data = Ticket.objects.values('category').annotate(count=Count('id'))
        for item in category_data:
            category_breakdown[item['category']] = item['count']

        # Ensure all choices are present with 0 if no tickets
        for choice in Ticket.Category.values:
            if choice not in category_breakdown:
                category_breakdown[choice] = 0

        data = {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "avg_tickets_per_day": round(avg_tickets_per_day, 2),
            "priority_breakdown": priority_breakdown,
            "category_breakdown": category_breakdown
        }

        return Response(data)
