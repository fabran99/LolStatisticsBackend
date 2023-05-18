from rest_framework import serializers

class getMatchlistSerializer(serializers.Serializer):
    limit = serializers.IntegerField(required=False, default=20)
    username = serializers.CharField(required=True)
    region = serializers.CharField(required=True)
    puuid = serializers.CharField(required=False)