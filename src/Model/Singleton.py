# Code credit to https://www.datacamp.com/community/tutorials/python
# -metaclasses


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = \
                super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

# To use this class, create a child class with the keyword argument
# metaclass=Singleton. For example, class PatientDictContainer(
# metaclass=Singleton): class definition
