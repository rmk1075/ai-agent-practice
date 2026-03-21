from django.http import StreamingHttpResponse
from django.shortcuts import render

from chat.service import fake_agent_stream

# Create your views here.
def chat_stream(request):
    message = request.GET.get("message", "")

    def event_stream():
        for token in fake_agent_stream(message):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream"
    )
