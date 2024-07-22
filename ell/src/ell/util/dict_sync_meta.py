from dataclasses import dataclass, fields


class DictSyncMeta(type):
    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)
        original_init = getattr(new_class, "__init__")

        def new_init(self, *args, **kwargs):
            # Set the fields first before the original __init__ is called
            for name, field in attrs.get("__annotations__", {}).items():
                if name in kwargs:
                    setattr(self, name, kwargs[name])
                else:
                    # Set default values for fields not provided in kwargs
                    default = field.default if hasattr(field, "default") else None
                    setattr(self, name, default)

            # Call the original __init__
            original_init(self, *args, **kwargs)

            # Now sync the fields to the dictionary
            for field in fields(self):
                self[field.name] = getattr(self, field.name)

        setattr(new_class, "__init__", new_init)

        original_setattr = getattr(new_class, "__setattr__")

        def new_setattr(self, key, value):
            original_setattr(self, key, value)
            if (
                key in self.__annotations__
            ):  # Only sync if it's a defined dataclass field
                self[key] = value

        setattr(new_class, "__setattr__", new_setattr)
        return new_class
