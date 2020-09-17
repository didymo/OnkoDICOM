# Code credit to https://www.datacamp.com/community/tutorials/python-metaclasses


class Singleton(type):
    _instances = {}

    def __call__(self, cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
