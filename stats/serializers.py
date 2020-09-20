from rest_framework import serializers

class GetRuneByID(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    elo = serializers.CharField()