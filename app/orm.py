import sqlalchemy
from sqlalchemy.orm import class_mapper


def object_as_dict(obj):
    return {
        c.key: getattr(obj, c.key)
        for c in sqlalchemy.inspect(obj).mapper.column_attrs
    }


def object_as_dict_with_rel(obj):
    columns = [c.key for c in class_mapper(obj.__class__).columns]
    relationships = {
        name: relation
        for name, relation in obj.__mapper__.relationships.items()
        if relation.uselist
    }
    data = {key: getattr(obj, key) for key in columns}

    for name, relation in relationships.items():
        data[name] = [
            object_as_dict_with_rel(item) for item in getattr(obj, name)
        ]

    return data
