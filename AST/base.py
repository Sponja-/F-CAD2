from typing import Dict, Iterable, Optional, Callable, List, Type
from abc import ABC, abstractmethod
from inspect import getfullargspec
from functools import wraps

forward_declarations = {}
prim_types = 


class Object:
    def __init__(self, type: "Class") -> None:
        self.type = type
        self.attributes: Dict[str, "Type[Object]"] = {}
        self.is_return = False
        self.is_except = False

    def __hash__(self):
        return self.type.get_method("#hash").eval({"this": self}).value

    def __repr__(self):
        return self.type.get_method("#to_string").eval({"this": self}).value

    def call(self, name: str, scope_path: tuple = (), args: List[Type["Object"]] = []) -> Type["Object"]:
        return MethodCall(Constant(self), name, [Constant(arg) for arg in args]).eval(())


class IComputable(ABC):
    @abstractmethod
    def eval(self, scope_path: tuple) -> Type[Object]:
        pass


class IAssignable(ABC):
    @abstractmethod
    def set_value(self, scope_path: tuple, value: Type[Object]) -> None:
        pass


class Constant(IComputable):
    def __init__(self, value: Type[Object]) -> None:
        self.value = value

    def eval(self, scope_path: tuple) -> Type[Object]:
        return self.value


class Scope:
    scope_n = 0

    def __init__(self,
                 elements: Dict[str, Type[Object]] = {}):
        self.elements = elements

    def __getitem__(self, path: tuple) -> Type[Object]:
        if len(path) > 1:
            return self.elements[path[0]][path[1:]] or self.elements.get(path[-1], None)
        return self.elements.get(path[0], None)

    def __setitem__(self, path: tuple, value: Type[Object]) -> None:
        if path[-1] in self.elements:
            self.elements[path[-1]] = value
        if len(path) > 1:
            self.elements[path[0]][path[1:]] = value
        else:
            self.elements[path[0]] = value

    def __delitem__(self, path: tuple) -> None:
        if len(path) > 1:
            del self.elements[path[0]][path[1:]]
        else:
            del self.elements[path[0]]

    def new_scope(self, path: tuple, elements: Dict[str, Type[Object]] = {}) -> tuple:
        if len(path > 1):
            return (path[0],) + self.elements[path[0]].new_scope(path[1:], elements)
        else:
            result = Scope.scope_n
            self.elements[path[0]] = Scope(elements)
            return (path[0], result)


class CreatePath:
    def __init__(self, path: tuple, elements: Dict[str, Type[Object]]) -> None:
        self.path = path
        self.elements = elements

    def __enter__(self):
        self.new_path = Variable.table.new_scope(self.path, self.elements)
        return self.new_path

    def __exit__(self):
        del Variable.table[self.new_path]


class Variable(IComputable, IAssignable):
    table = Scope()

    def __init__(self, name: str) -> None:
        self.name = name

    def eval(self, scope_path: tuple) -> Type[Object]:
        result = Variable.table[scope_path + (self.name,)]
        if result is not None:
            return result
        raise f"Name {self.name} could not be resolved"

    def set_value(self, scope_path: tuple, value: Object):
        Variable.table[scope_path + (self.name,)] = value


def create_locals(names: List[str],
                  args: List[Type[Object]],
                  var_arg_name: Optional[str]):
    new_locals = {name: arg for name, arg in zip(names, args)}
    if var_arg_name is not None:
        new_locals[var_arg_name] = forward_declarations["array"](args[len(names):])

    return new_locals


class FunctionCall(IComputable):  # Or FunctionCall
    def __init__(self,
                 function: Type[IComputable],
                 arguments: Iterable[IComputable]) -> None:
        self.function = function
        self.arguments = arguments

    def eval(self, scope_path: tuple) -> Type[Object]:
        f = self.function.eval(scope_path)
        assert(len(f.arg_names) <= len(self.arguments))

        new_locals = create_locals(f.arg_names,
                                   [arg.eval(scope_path) for arg in self.arguments],
                                   f.var_arg_name)

        with CreatePath(scope_path, new_locals) as new_path:
            result = f.operation.eval(new_path)
            result.is_return = False
            return result


class MethodCall(IComputable):
    def __init__(self,
                 object: Type[IComputable],
                 method_name: str,
                 arguments: Iterable[IComputable]):
        self.object = object
        self.method_name = method_name
        self.arguments = arguments

    def eval(self, scope_path: tuple) -> Type[Object]:
        obj = self.object.eval(scope_path)
        method = obj.type.get_method(self.method_name)
        assert(len(method.arg_names) <= len(self.arguments))

        new_locals = create_locals(method.arg_names,
                                   [arg.eval(scope_path) for arg in self.arguments],
                                   method.var_arg_name)
        new_locals["this"] = obj

        with CreatePath(scope_path, new_locals) as new_path:
            result = method.operation.eval(new_path)
            result.is_return = False
            return result


class MemberAccess(IComputable, IAssignable):
    def __init__(self, object: Type[IComputable], name: str) -> None:
        self.object = object
        self.name = name

    def eval(self, scope_path: tuple) -> Type[Object]:
        obj = self.object.eval(scope_path)
        if self.name in obj.attributes:
            return obj.attributes[self.name]
        elif self.name in obj.type.methods:
            return obj.type.methods[self.name]
        elif self.name in obj.type.static_attributes:
            return obj.type.static_attributes[self.name]
        raise f"Class {obj.type} has no attribute \"{self.name}\""

    def set_value(self, scope_path, value: Object) -> None:
        self.object.eval(scope_path).attributes[self.name] = value


class IPrimitiveType(Object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PrimitiveCall(IComputable):
    def __init__(self,
                 function: Callable[[tuple], Type[Object]]) -> None:
        self.function = function

    def eval(self, scope_path: tuple) -> Type[Object]:
        return self.function(scope_path)


def to_primitive_function(func: Callable) -> "Function":
    specs = getfullargspec(func)

    arg_names = specs[0]
    var_arg_name = specs[1]

    @wraps(func)
    def primitive_func(scope_path: tuple):
        if var_arg_name is None:
            return func(*[Variable(name).eval(scope_path) for name in arg_names])
        else:
            return func(*[Variable(name).eval(scope_path) for name in arg_names],
                        *Variable(var_arg_name).eval(scope_path).elements)

    return Function([name for name in arg_names if name != "this"],
                    PrimitiveCall(primitive_func),
                    var_arg_name=var_arg_name)


class Class(IPrimitiveType):
    def __init__(self,
                 name: str,
                 methods: Dict[str, "Function"],
                 statics: Dict[str, "Type[Object]"],
                 parent: Optional["Class"] = None) -> None:
        self.name = name
        self.methods = methods
        self.static_attributes = statics
        self.parent = parent
        super().__init__(class_class)

    def has_method(self, name: str) -> bool:
        return (name in self.methods or
                (self.parent is not None and self.parent.has_method(name)))

    def get_method(self, name: str) -> "Function":
        if name in self.methods:
            return self.methods[name]
        elif self.parent is not None:
            return self.parent.get_method(name)
        raise f"Class {self.name} has no method \"{name}\""


class_class = Class("class", {}, {})


class Function(IPrimitiveType):
    def __init__(self,
                 arg_names: Iterable[str],
                 operation: "Type[IComputable]",
                 **kwargs) -> None:
        self.arg_names = arg_names
        self.operation = operation
        self.var_arg_name = kwargs.get("var_arg_name", None)
        super().__init__(function_class)


function_class = Class("function", {}, {})


def best_fitting_method(operator_name, obj, pos, length):
    if obj.type.has_method(operator_name + f"_{str(pos)}"):
        return (obj.type.get_method(operator_name + f"_{str(pos)}"), True)
    elif pos == 0 and length == 2 and obj.type.has_method(operator_name + "_left"):
        return (obj.type.get_method(operator_name + "_left"), True)
    elif pos == 1 and length == 2 and obj.type.has_method(operator_name + "_right"):
        return (obj.type.get_method(operator_name + "_left"), True)

    if obj.type.has_method(operator_name):
        return (obj.type.get_method(operator_name), False)

    return None


def resolve_overload(operator_name, objects):
    best_method = None
    owner = None
    position = 0
    is_prim = True
    has_pos = False
    for i, obj in enumerate(objects):  # First pass checks non prim for correct positions
        method, with_pos = best_fitting_method(operator_name, obj, i, len(objects))
        if method is not None:
            primitive = isinstance(obj, IPrimitiveType)
            if (best_method is None or
               is_prim and not primitive or
               not is_prim and not primitive and not has_pos and with_pos or
               is_prim and not has_pos and with_pos):
                best_method = method
                owner = obj
                position = i

    return (best_method, owner, position)


class OperatorCall(IComputable):
    def __init__(self, name: str, arguments: Iterable[Type[IComputable]]) -> None:
        self.name = name
        self.arguments = arguments

    def eval(self, scope_path: tuple) -> Type[Object]:
        objs: List[Object] = [arg.eval(scope_path) for arg in self.arguments]

        method, owner, position = resolve_overload(self.name, objs)

        if method is None:
            raise f"Cant perform {self.name} on objects of types\
                    {', '.join([str(obj.type) for obj in objs])}"

        del objs[position]

        new_locals = create_locals(method.arg_names,
                                   objs,
                                   method.var_arg_name)
        new_locals["this"] = owner

        with CreatePath(scope_path, new_locals) as new_path:
            result = method.operation.eval(new_path)
            result.is_return = False
            return result


none_class = Class("none", {}, {})


class NoneType(IPrimitiveType):
    def __init__(self) -> None:
        super().__init__(none_class)


none_object = NoneType()


def unpack(obj: Type[Object]) -> List[Type[Object]]:
    result = []
    iterator = obj.call("#iter")
    value = iterator.call("#next")
    while type(value) is not forward_declarations["StopIteration"]:
        result.append(value)
        value = iterator.call("#next")


class Assignment(IComputable):
    def __init__(self, object: Type[IComputable], value: Type[IComputable]) -> None:
        self.object = object
        self.value = value

    def eval(self, scope_path: tuple) -> Type[Object]:
        value = self.value.eval(scope_path)
        self.object.eval(scope_path).set_value(value)
        return value


class ConstructorCall(IComputable):
    def __init__(self, type: IComputable, arguments: List[IComputable]):
        self.type = type
        self.arguments = arguments

    def eval(self, scope_path):
        if self.type.name in forward_declarations:
            new_obj = forward_declarations[self.type.name]()
        else:
            new_obj = Object(type)

        constructor = self.type.get_method("#new")

        new_locals = create_locals(constructor.arg_names,
                                   [arg.eval(scope_path) for arg in self.arguments],
                                   constructor.var_arg_name)
        new_locals["this"] = new_obj

        with CreatePath(scope_path, new_locals) as new_path:
            constructor.operation.eval(new_path)
            new_obj.is_return = False
            return new_obj


class CreateClass(IComputable):
    def __init__(self,
                 name: str,
                 method_assignments: List[IComputable],
                 static_assignments: List[IComputable],
                 parent: Optional[IComputable] = None) -> None:
        self.name = name
        self.method_assignments = method_assignments
        self.static_assignments = static_assignments
        self.parent = parent

    def eval(self, scope_path: tuple):
        return Class(self.name.value,
                     {m.object.name: m.value.eval(scope_path) for m in self.method_assignments},
                     {s.object.name: s.value.eval(scope_path) for s in self.static_assignments},
                     self.parent.eval(scope_path))


def register_primitive(name, cls, type):
    Variable.table[(name,)] = type
    forward_declarations[name] = cls


register_primitive("class", Class, class_class)
register_primitive("function", Function, function_class)
register_primitive("NoneType", NoneType, none_class)
