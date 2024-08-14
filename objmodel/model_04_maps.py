MISSING = object()


class Base:
    """The base class that all of the object model classes inherit from."""

    def __init__(self, cls: "Class", fields):
        """Every object has a class."""
        self.cls = cls
        # Wait... does each instance store field names?
        self._fields = fields

    def read_attr(self, fieldname):
        """read field 'fieldname' out of the object"""
        result = self._read_dict(fieldname)
        if result is not MISSING:
            return result
        result = self.cls._read_from_class(fieldname)
        if _is_bindable(result):
            return _make_boundmethod(result, self)
        if result is not MISSING:
            return result
        meth = self.cls._read_from_class("__getattr__")
        if meth is not MISSING:
            return meth(self, fieldname)
        raise AttributeError(fieldname)

    def write_attr(self, fieldname, value):
        """write field 'fieldname' into the object"""
        result = self.cls._read_from_class("__setattr__")
        if result is not MISSING:
            return result(self, fieldname, value)
        self._write_dict(fieldname, value)

    def write_attr(self, fieldname, value):
        """write field 'fieldname' into the object"""
        self._write_dict(fieldname, value)

    def isinstance(self, cls):
        """return True if the object is an instance of class cls"""
        return self.cls.issubclass(cls)

    def callmethod(self, methname, *args):
        """call method 'methname' with arguments 'args' on object"""
        meth = self.cls._read_from_class(methname)
        return meth(self, *args)

    def _read_dict(self, fieldname):
        return self._fields.get(fieldname, MISSING)

    def _write_dict(self, fieldname, value):
        self._fields[fieldname] = value


def _is_bindable(meth):
    return hasattr(meth, "__get__")


def _make_boundmethod(meth, self):
    return meth.__get__(self, None)


class Instance(Base):
    """Instance of a user-defined class."""

    def __init__(self, cls):
        assert isinstance(cls, Class)
        Base.__init__(self, cls, {})


class Class(Base):
    def __init__(self, name, base_class: "Class", fields, metaclass):
        Base.__init__(self, metaclass, fields)
        self.name = name
        self.base_class = base_class

    def method_resolution_order(self):
        """Compute the method resolution order of the class"""
        if self.base_class is None:
            return [self]
        else:
            return [self] + self.base_class.method_resolution_order()

    def issubclass(self, cls):
        return cls in self.method_resolution_order()

    def _read_from_class(self, methname):
        for cls in self.method_resolution_order():
            if methname in cls._fields:
                return cls._fields[methname]
        return MISSING


# set up the base hierarchy like in Python (the ObjVLisp model)
# the ultimate base class is OBJECT
def OBJECT__setattr__(self: Base, fieldname, value):
    self._write_dict(fieldname, value)


OBJECT = Class("OBJECT", None, {"__setattr__": OBJECT__setattr__}, None)
# TYPE is a subclass of OBJECT
TYPE = Class(name="TYPE", base_class=OBJECT, fields={}, metaclass=None)
# TYPE is an instance of itself
TYPE.cls = TYPE
# OBJECT is an instance of TYPE
OBJECT.cls = TYPE
