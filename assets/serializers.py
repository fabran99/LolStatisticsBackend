from rest_framework import serializers

class GetChampAssetsSerializer(serializers.Serializer):
    champ_id = serializers.IntegerField(required=True)