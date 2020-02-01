from typing import Dict, Iterable, Optional, Callable, List, Type
from abc import ABC, abstractmethod
from inspect import getfullargspec
from functools import wraps

forward_declarations = {}


class Class:
    table: Dict[str, "Class"] = {}

    def __init__(self,
                 name: str,
                 methods: Dict[str, "Function"],
                 statics: Dict[str, "Type[Object]"],
                 parent: Optional["Class"] = None) -> None:
        self.name = name
        self.methods = methods
        self.static_attributes = statics
        self.parent = parent
        Class.table[name] = self

    def has_method(self, name: str) -> bool:
        return (name in self.methods or
                (self.parent is not None and self.parent.has_method(name)))

    def get_method(self, name: str) -> "Function":
        if name in self.methods:
            return self.methods[name]
        elif self.parent is not None:
            return self.parent.get_method(name)
        raise f"Class {self.name} has no method \"{name}\""


class Object:
    def __init__(self, type: Class) -> None:
        self.type = type
        self.attributes: Dict[str, "Type[Object]"] = {}
        self.is_return = False


function_class = Class("function", {}, {})


class Function(Object):
    def __init__(self,
                 arg_names: Iterable[str],
                 operation: "Type[IComputable]",
                 **kwargs) -> None:
        self.arg_names = arg_names
        self.operation = operation
        self.var_arg_name = kwargs.get("var_arg_name", None)
        super().__init__(function_class)


class IComputable(ABC):
    @abstractmethod
    def eval(self, locals: Dict[str, Type[Object]]) -> Object:
        pass


class IAssignable(ABC):
    @abstractmethod
    def set_value(self, value: Type[Object]) -> None:
        pass


class Constant(IComputable):
    def __init__(self, value: Type[Object]) -> None:
        self.value = value

    def eval(self, locals: Dict[str, Type[Object]]) -> Object:
        return self.value


class Variable(IComputable, IAssignable):
    table: Dict[str, "Variable"] = {}

    def __init__(self, name: str) -> None:
        self.name = name

    def eval(self, locals: Dict[str, Type[Object]]) -> Object:
        if self.name in locals:
            return locals[self.name]
        if self.name in Variable.table:
            return Variable.table[self.name]
        raise f"Name \"{self.name}\" not recognized"

    def set_value(self, value: Object):
        Variable.table[self.name] = value


class MethodCall(IComputable):  # Or FunctionCall
    def __init__(self,
                 object: Optional[IComputable],
                 function: Type[IComputable],
                 arguments: Iterable[IComputable]) -> None:
        self.object = object
        self.function = function
        self.arguments = arguments

    def eval(self, locals: Dict[str, Type[Object]]) -> Object:
        f = self.function.eval(locals)
        assert(len(f.arg_names) <= len(self.arguments))
        new_locals = {name: arg.eval(locals)
                      for name, arg in zip(f.arg_names, self.arguments)}
        if f.var_arg_name is not None:
            new_locals[f.var_arg_name] = forward_declarations["Array"](
                [arg.eval(locals) for arg in self.arguments[len(f.arg_names):]]
            )
        if self.object is not None:
            new_locals["this"] = self.object.eval(locals)
        return f.operation.eval(new_locals)


class MemberAccess(IComputable, IAssignable):
    def __init__(self, object: Type[IComputable], name: str) -> None:
        self.object = object
        self.name = name

    def eval(self, locals: Dict[str, Type[Object]]) -> Object:
        obj = self.object.eval(locals)
        if self.name in obj.attributes:
            return obj.attributes[self.name]
        elif self.name in obj.type.methods:
            return obj.type.methods[self.name]
        elif self.name in obj.type.static_attributes:
            return obj.type.static_attributes[self.name]
        raise f"Class {obj.type} has no attribute \"{self.name}\""

    def set_value(self, value: Object) -> None:
        self.object.eval(locals).attributes[self.name] = value


class IPrimitiveType(Object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PrimitiveCall(IComputable):
    def __init__(self,
                 function: Callable[[Dict[str, Type[Object]]], Type[Object]]) -> None:
        self.function = function

    def eval(self, locals: Dict[str, Type[Object]]) -> Object:
        return self.function(locals)


def to_primitive_function(func: Callable) -> Function:
    specs = getfullargspec(func)

    arg_names = specs[0]
    var_arg_name = specs[1]

    @wraps(func)
    def primitive_func(locals):
        if var_arg_name is None:
            return func(*[locals[name] for name in arg_names])
        else:
            return func(*[locals[name] for name in arg_names],
                        *locals[var_arg_name].elements)

    return Function([name for name in arg_names if name != "this"],
                    PrimitiveCall(primitive_func),
                    var_arg_name=var_arg_name)


class OperatorCall(IComputable):
    def __init__(self, name: str, arguments: Iterable[Type[IComputable]]) -> None:
        self.name = f"operator_{name}"
        self.arguments = arguments

    def eval(self, locals: Dict[str, Type[Object]]) -> Object:
        objs: List[Object] = [arg.eval(locals) for arg in self.arguments]
        method = None
        owner_of_method = None
        position = 0

        if len(self.arguments == 2) and objs[0].type.has_method(self.name + "_left"):
            method = objs[0].type.get_method(self.name + "_left")
            owner_of_method = objs[0]
            position = 0
        elif len(self.arguments == 2) and objs[1].type.has_method(self.name + "_right"):
            method = objs[1].type.get_method(self.name + "_right")
            owner_of_method = objs[1]
            position = 1
        else:
            for i, obj in enumerate(objs):
                if not isinstance(obj, IPrimitiveType):
                    if obj.type.has_method(self.name):
                        owner_of_method = obj
                        method = obj.type.get_method(self.name)
                        position = i
                        break
                elif method is None:
                    if obj.type.has_method(self.name):
                        owner_of_method = obj
                        method = obj.type.get_method(self.name)
                        position = i

        if method is None:
            raise f"Cant perform {self.name} on objects of types\
                    {', '.join([str(obj.type) for obj in objs])}"

        del objs[position]

        new_locals = {name: obj for name, obj in zip(method.arg_names, objs)}

        if method.var_arg_name is not None:
            new_locals[method.var_arg_name] = forward_declarations["Array"](objs[len(method.arg_names) - 1:])  # TODO

        new_locals["this"] = owner_of_method

        return method.operation.eval(new_locals)


none_class = Class("none", {}, {})


class NoneType(IPrimitiveType):
    def __init__(self) -> None:
        super().__init__(none_class)


none_object = NoneType()
