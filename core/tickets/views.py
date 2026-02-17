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



from django.conf import settings
from groq import Groq, APIError
import json

class TicketClassifyView(views.APIView):
    def post(self, request):
        description = request.data.get('description')
        if not description:
            return Response(
                {"error": "Description is required."},
                status=400
            )

        api_key = getattr(settings, 'GROQ_API_KEY', None)
        if not api_key:
             return Response(
                {
                    "suggested_category": None,
                    "suggested_priority": None,
                    "error": "Groq API key not configured."
                },
                status=200 
            )

        client = Groq(api_key=api_key)
        
        prompt = f"""
        Analyze the following ticket description and suggest a category and priority.
        
        Description: "{description}"
        
        Allowed Categories: billing, technical, account, general
        Allowed Priorities: low, medium, high, critical
        
        Return ONLY a JSON object with keys "suggested_category" and "suggested_priority".
        Example: {{"suggested_category": "technical", "suggested_priority": "high"}}
        """

        try:
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You are a helpful support ticket classifier."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.3,
            )
            content = response.choices[0].message.content.strip()
            # Handle potential markdown code blocks in response
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '')
            
            data = json.loads(content)
            
            return Response({
                "suggested_category": data.get("suggested_category"),
                "suggested_priority": data.get("suggested_priority")
            })

        except (APIError, json.JSONDecodeError, Exception) as e:
            # Log error in production
            return Response({
                "suggested_category": None,
                "suggested_priority": None
            })
