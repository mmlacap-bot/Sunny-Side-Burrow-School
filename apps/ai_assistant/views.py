import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .models import AIRequestLog
from .services import GeminiService


@login_required
@require_http_methods(["GET", "POST"])
def teacher_ai_assistance(request):
    if request.method == "GET":
        return render(
            request,
            "ai_assistant/teacher_ai_assistance.html",
            {"active_page": "ai"}
        )

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            question = data.get("question", "").strip()
        except Exception:
            question = request.POST.get("question", "").strip()

        if not question:
            return JsonResponse({
                "success": False,
                "error": "Question cannot be empty."
            })

        try:
            service = GeminiService()
        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e),
                "response": None,
                "tokens_used": 0,
                "response_time": 0
            })

        result = service.get_response(question)

        try:
            teacher = request.user.teacher
        except Exception:
            teacher = None

        AIRequestLog.objects.create(
            teacher=teacher,
            question=question,
            response=result.get("response") or "",
            tokens_used=result.get("tokens_used", 0),
            response_time_seconds=result.get("response_time", 0),
            was_successful=result.get("success", False)
        )

        return JsonResponse(result)
