import logging
from django.db import models
from django.db.models.query import QuerySet

class DataMapper:
    def __init__(self, config, target_model=None, enable_logging=False):
        self.config = config
        self.target_model = target_model
        self.enable_logging = enable_logging
        self.logger = logging.getLogger(__name__)
    
    def map_data(self, data, default_values={}, dont_save=False):
        mapped_data = {}
        for mapping in self.config:
            to_field = mapping.get('to_field')
            
            from_field = mapping.get('from_field')
            default_value = mapping.get('default_value')

            compute_method = mapping.get('compute_method')

            mapper = mapping.get("mapper")

            if from_field and compute_method:
                raise ValueError("Both from_field and compute_field should be provided at same time, because it's conflicting")

            if from_field:
                try:
                    value = self.get_value(data, from_field, mapper=mapper, dont_save=dont_save)
                    mapped_data = self.set_value(mapped_data, to_field, value)
                except KeyError:
                    if default_value is not None:
                        mapped_data = self.set_value(mapped_data, to_field, default_value)

            elif compute_method:
                value = compute_method(data)
                mapped_data = self.set_value(mapped_data, to_field, value)
            else:
                raise ValueError("from_field or compute_method should be provided")

        if default_values:
            mapped_data.update(default_values)

        if self.target_model:
            instance = self.create_instance(self.target_model, mapped_data, default_values=default_values, dont_save=dont_save)
            self.logger.info(f"Created instance of {self.target_model.__name__}")
            return instance
        else:
            return mapped_data
    
    def get_value(self, data, field, mapper=None, dont_save=False):
        current_data = data
        for f in field.split('__'):
            if isinstance(data, models.Model):
                current_data = getattr(current_data, field)
            else:
                current_data = current_data.get(f)
        
        if isinstance(current_data, QuerySet) or isinstance(current_data, list):
            unserialized_data = current_data
            current_data = []
            if mapper == 'self':
                m2m_mapper = DataMapper(self.config, target_model=self.target_model, enable_logging=self.enable_logging)
            elif isinstance(mapper, dict):
                m2m_mapper = DataMapper(self.config, enable_logging=self.enable_logging)
            else:
                m2m_mapper = mapper
            
            for m2m_instance in unserialized_data:
                serialized_instance = m2m_mapper.map_data(m2m_instance, dont_save=dont_save)
                current_data.append(serialized_instance)

        return current_data
    
    def set_value(self, data, field, value):
        fields = field.split('__')
        for f in fields[:-1]:
            if f not in data:
                data[f] = {}
            data = data[f]
        data[fields[-1]] = value
        return data
    
    def create_instance(self, model, data, default_values={}, dont_save=False):
        instance_kwargs = {}
        m2m_fields = {}
        for key, value in data.items():
            if value is None:
                continue

            if isinstance(value, dict):
                field = model._meta.get_field(key)
                related_model = field.related_model

                related_model_instance = self.create_instance(related_model, value)
                instance_kwargs[key] = related_model_instance
            elif isinstance(value, list) or isinstance(value, QuerySet):
                field = model._meta.get_field(key)
                related_model = field.related_model

                for single_value in value:
                    if not dont_save:
                        related_model_instance = single_value
                        related_m2m_field = {}
                    else:
                        related_model_instance = single_value[0]
                        related_m2m_field = single_value[1]

                    if not isinstance(related_model_instance, related_model):
                        related_data = self.create_instance(related_model, related_model_instance, dont_save=dont_save)

                        if dont_save:
                            related_model_instance = related_data[0]
                            related_m2m_field = related_data[1]
                        else:
                            related_m2m_field = {}
                            related_model_instance = related_data
                    
                    related_data = related_model_instance
                    if dont_save:
                        related_data = related_model_instance, related_m2m_field
                    
                    if key in m2m_fields:
                        m2m_fields[key].append(related_data)
                    else:
                        m2m_fields[key] = [related_data]

            else:
                instance_kwargs[key] = value
        
        instance_kwargs.update(default_values)

        if not dont_save:
            instance = model.objects.create(**instance_kwargs)

            save_again =  False
            for m2m_field in m2m_fields:
                getattr(instance, m2m_field).add(*m2m_fields[m2m_field])
                save_again = True

            if save_again:
                instance.save()

            return instance
        else:
            instance = model(**instance_kwargs)

            return instance, m2m_fields
