from rest_framework import serializers

class NotificationSerializer(serializers.Serializer):
    notification_id = serializers.CharField()
    type = serializers.CharField()
    data = serializers.JSONField()