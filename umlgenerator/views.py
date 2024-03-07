from rest_framework.response import Response
from rest_framework.decorators import api_view
import json

from .ai_functions import generate, classes_set, attributes_set, methods_set


@api_view(['POST'])
def umlGenerator(request):
    try:
        text = json.loads(request.body)['text']
    except:
        return Response({"message": "Invalid Input"}, 400)

    generate(text)
    entities = []
    for candidate_class in classes_set:
        entity = {"name": candidate_class}

        if candidate_class in attributes_set.keys():
            entity["attributes"] = attributes_set[candidate_class]
        if candidate_class in methods_set.keys():
            entity["methods"] = methods_set[candidate_class]

        entities.append(entity)

    return Response(entities)
