from django.urls import path
from .views import AnalyzeView, SuggestView, FeedbackView

urlpatterns = [
    path("analyze/", AnalyzeView.as_view(), name="analyze"),
    path("suggest/", SuggestView.as_view(), name="suggest"),
    path("feedback/", FeedbackView.as_view(), name="feedback"),   # NEW
]
