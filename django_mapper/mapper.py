from typing import Callable, Dict, Optional
from django.db import models


class DataMapper:
    def __init__(self, from_model: models.Model, to_model: models.Model):
        self.from_model = from_model
        self.to_model = to_model
        self.mappings = []

    def map_data(self, from_field: str, to_field: str, nullable: Optional[bool] = False) -> None:
        self.mappings.append({
            'from_field': from_field,
            'to_field': to_field,
            'nullable': nullable,
        })

    def map_data_with_function(self, from_field: str, to_field: str, function: Callable, nullable: Optional[bool] = False) -> None:
        self.mappings.append({
            'from_field': from_field,
            'to_field': to_field,
            'function': function,
            'nullable': nullable,
        })

    def map_from_config(self, from_instance: models.Model) -> models.Model:
        to_instance = self.to_model()
        for mapping in self.mappings:
            from_fields = mapping['from_field'].split('__')
            from_value = from_instance
            for field in from_fields:
                from_value = getattr(from_value, field)
            if mapping.get('function'):
                from_value = mapping['function'](from_value)
            if not mapping['nullable'] and not from_value:
                raise ValueError(f"{from_instance} has a NULL value for a non-nullable field {mapping['from_field']}")
            setattr(to_instance, mapping['to_field'], from_value)
        return to_instance

    def map_all_data(self):
        from_instances = self.from_model.objects.all()
        to_instances = []
        for from_instance in from_instances:
            to_instance = self.map_from_config(from_instance)
            to_instances.append(to_instance)
        self.to_model.objects.bulk_create(to_instances)


def create_mapper(config: Dict) -> DataMapper:
    from_model = config['from_model']
    to_model = config['to_model']
    mappings = config['mappings']

    mapper = DataMapper(from_model, to_model)
    for mapping in mappings:
        from_field = mapping['from_field']
        to_field = mapping['to_field']
        nullable = mapping.get('nullable', False)
        if mapping.get('function'):
            function = mapping['function']
            mapper.map_data_with_function(from_field, to_field, function, nullable)
        else:
            mapper.map_data(from_field, to_field, nullable)
    return mapper

