import logging

class DataMapper:
    def __init__(self, config, target_model=None, enable_logging=False):
        self.config = config
        self.target_model = target_model
        self.enable_logging = enable_logging
        self.logger = logging.getLogger(__name__)
    
    def map_data(self, data):
        mapped_data = {}
        for mapping in self.config:
            to_field = mapping.get('to_field')
            
            from_field = mapping.get('from_field')
            default_value = mapping.get('default_value')

            compute_method = mapping.get('compute_method')

            if to_field and compute_method:
                raise ValueError("Both from_field and compute_field should be provided at same time, because it's conflicting")

            if to_field:
                try:
                    value = self.get_value(data, from_field)
                    mapped_data = self.set_value(mapped_data, to_field, value)
                except KeyError:
                    if default_value is not None:
                        mapped_data = self.set_value(mapped_data, to_field, default_value)

            elif compute_method:
                value = compute_method(value, data)
                mapped_data = self.set_value(mapped_data, to_field, value)
            else:
                raise ValueError("from_field or compute_method should be provided")

        if self.target_model:
            instance = self.create_instance(self.target_model, mapped_data)
            self.logger.info(f"Created instance of {self.target_model.__name__}")
            return instance
        else:
            return mapped_data
    
    def get_value(self, data, field):
        for f in field.split('__'):
            data = data.get(f)
        return data
    
    def set_value(self, data, field, value):
        fields = field.split('__')
        for f in fields[:-1]:
            if f not in data:
                data[f] = {}
            data = data[f]
        data[fields[-1]] = value
        return data
    
    def create_instance(self, model, data):
        instance_kwargs = {}
        for key, value in data.items():
            if isinstance(value, dict):
                field = getattr(instance, key)
                related_model = field.related_model

                related_model_instance = self.create_instance(related_model, value)
                instance_kwargs[key] = related_model_instance
            else:
                instance_kwargs[key] = value
        
        instance = model.objects.create(**instance_kwargs)
        return instance
