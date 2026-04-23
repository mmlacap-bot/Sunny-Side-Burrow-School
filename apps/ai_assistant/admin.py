from django.contrib import admin

from .models import AIRequestLog


@admin.register(AIRequestLog)
class AIRequestLogAdmin(admin.ModelAdmin):
    list_display = [
        'teacher',
        'question_preview',
        'tokens_used',
        'was_successful',
        'response_time_seconds',
        'created_at',
    ]
    list_filter = ['was_successful', 'created_at']
    search_fields = ['question', 'response', 'teacher__user__username']

    def question_preview(self, obj):
        return obj.question[:50] + ('...' if len(obj.question) > 50 else '')
    question_preview.short_description = 'Question Preview'
