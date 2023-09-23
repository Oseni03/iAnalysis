from rest_framework import serializers


class TrialExpiresSoonEmailSerializer(serializers.Serializer):
    expiry_date = serializers.DateTimeField()
    domain = serializers.CharField()
    site_name = serializers.CharField()


class SubscriptionErrorSerializer(serializers.Serializer):
    domain = serializers.CharField()
    site_name = serializers.CharField()