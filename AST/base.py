from typing import Dict, Iterable, Optional, Callable, List, Type, Union
from abc import ABC, abstractmethod
from inspect import getfullargspec
from functools import wraps

forward_declarations = {}
class_class_created = False


class Object:
    def __init__(self, type: "Class") -> None:
        self.type = type
        self.attributes = {name: get_bound_function(method, self) for name, method in self.type.object_methods().items()}
        self.is_return = False
        self.is_except = False

    def call(self, name: str, scope_path: tuple = (), args: List[Type["Object"]] = []) -> Type["Object"]:
        return FunctionCall(Constant(self.attributes[name]), [Constant(arg) for arg in args]).eval(scope_path)

    def __getitem__(self, index):
        return self.attributes[index]

    def __hash__(self):
        return self.call("#hash").value

    def __repr__(self):
        return self.call("#to_string").value

    def __iter__(self):
        return self.call("#iter")

    def __next__(self):
        result = self.call("#next")
        if result.type.name == "StopIteration":
            raise StopIteration
        else:
            return result


def get_bound_function(f, obj):
    return Function(f.operation,
                    f.parent_scope,
                    f.arg_names,
                    f.var_arg_name,
                    bound_object=obj)


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
                 elements: Dict[str, Union[Type[Object]], Type[IComputable], str] = {}):
        self.elements = dict(elements)

    def __getitem__(self, path: tuple) -> Type[Object]:
        if len(path) > 1:
            return self.elements[path[0]][path[1:]] or self.elements.get(path[-1], None)
        result = self.elements.get(path[0], None)
        if type(result) is str and result == "global":
            return Variable.table[path]
        else:
            return result

    def __setitem__(self, path: tuple, value: Type[Object]) -> None:
        if len(path) > 1:
            self.elements[path[0]][path[1:]] = value
        else:
            result = self.elements.get(path[0], None)
            if type(result) is str and result == "global":
                Variable.table[path] = value
            else:
                self.elements[path[0]] = value

    def __delitem__(self, path: tuple) -> None:
        if len(path) > 1:
            del self.elements[path[0]][path[1:]]
        else:
            del self.elements[path[0]]

    def new_scope(self,
                  path: tuple,
                  elements: Dict[str, Type[Object]] = {}) -> tuple:
        if len(path) > 0:
            return (path[0],) + self.elements[path[0]].new_scope(path[1:], elements)
        else:
            result = Scope.scope_n
            Scope.scope_n += 1
            self.elements[result] = Scope(elements)
            return (result,)


class CreateScope:
    def __init__(self, path: tuple, elements: Dict[str, Type[Object]]) -> None:
        self.path = path
        self.elements = elements

    def __enter__(self):
        self.new_path = Variable.table.new_scope(self.path, self.elements)
        return self.new_path

    def __exit__(self, type, value, traceback):
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


class Assignment(IComputable):
    def __init__(self, object: Type[IComputable], value: Type[IComputable]) -> None:
        self.object = object
        self.value = value

    def eval(self, scope_path: tuple) -> Type[Object]:
        value = self.value.eval(scope_path)
        self.object.set_value(scope_path, value)
        return value


class GlobalDeclare(IComputable):
    def __init__(self, name):
        self.name = name

    def eval(self, scope_path: tuple) -> Type[Object]:
        Variable(self.name).set_value(scope_path, "global")
        return none_object


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

    return Function(PrimitiveCall(primitive_func),
                    (),
                    [name for name in arg_names if name != "this"],
                    var_arg_name)


class Class(IPrimitiveType):
    def __init__(self,
                 name: str = "",
                 methods: Dict[str, "Function"] = {},
                 statics: Dict[str, Type[Object]] = {},
                 parent: Optional["Class"] = None) -> None:
        self.name = name
        self.methods = methods
        self.parent = parent
        if self.name != "class":
            super().__init__(class_class)
            self.attributes.update(statics)

    def object_methods(self):
        methods = {}
        if self.parent is not None:
            methods.update(self.parent.object_methods())
        methods.update(self.methods)
        return methods

    def has_method(self, name: str) -> bool:
        return (name in self.methods or
                (self.parent is not None and self.parent.has_method(name)))

    def get_method(self, name: str) -> "Function":
        if name in self.methods:
            return self.methods[name]
        elif self.parent is not None:
            return self.parent.get_method(name)
        raise f"Class {self.name} has no method \"{name}\""


class ClassCreate(IComputable):
    def __init__(self,
                 name: str,
                 methods: Dict[str, Type[IComputable]],
                 statics: Dict[str, Type[IComputable]],
                 parent_name: Optional[str]) -> None:
        self.name = name
        self.methods = methods
        self.statics = statics
        self.parent_name = parent_name

    def eval(self, scope_path: tuple) -> Class:
        return ConstructorCall(Constant(class_class), [
            Constant(self.name),
            Constant(forward_declarations["dict"](
                {forward_declarations["string"](name): value.eval(scope_path) for name, value in self.methods.items()}
            )),
            Constant(forward_declarations["dict"](
                {forward_declarations["string"](name): value.eval(scope_path) for name, value in self.statics.items()}
            )),
            Variable(self.parent_name) if self.parent is not None else none_class]).eval(scope_path)


def class_constructor(this: Class, name, methods, statics, parent):
    assert(name.type.name == "string")
    assert(methods.type.name == "dict")
    assert(statics.type.name == "dict")
    assert(parent.type.name == "class")
    this.name = name.value
    this.methods = {name.value: elem for name, elem in methods.elements.items()}
    this.parent = parent if parent.name != "NoneType" else None
    this.attributes.update({name.value: elem for name, elem in statics.elements.items()})


class ConstructorCall(IComputable):
    def __init__(self, type: IComputable, arguments: List[IComputable]) -> None:
        self.type = type
        self.arguments = arguments

    def eval(self, scope_path: tuple) -> Type[Object]:
        t = self.type.eval(scope_path)
        if t.name in forward_declarations:
            new_obj = forward_declarations[t.name]()
        else:
            new_obj = Object(t)

        if "constructor" in new_obj.attributes:
            constructor = new_obj.attributes["constructor"]

            new_locals = create_locals(constructor, [arg.eval(scope_path) for arg in self.arguments])

            with CreateScope(constructor.parent_scope, new_locals) as new_path:
                constructor.operation.eval(new_path)
                new_obj.is_return = False

        return new_obj


class MemberAccess(IComputable, IAssignable):
    def __init__(self, object: Type[IComputable], name: str) -> None:
        self.object = object
        self.name = name

    def eval(self, scope_path: tuple) -> Type[Object]:
        obj = self.object.eval(scope_path)
        if self.name in obj.attributes:
            return obj.attributes[self.name]
        raise f"Object {obj.type} has no attribute \"{self.name}\""

    def set_value(self, scope_path, value: Object) -> None:
        self.object.eval(scope_path).attributes[self.name] = value


class Function(IPrimitiveType):  # TODO: Optional/default arguments
    def __init__(self,
                 operation: Type[IComputable],
                 parent_scope: tuple,
                 arg_names: Iterable[str],
                 var_arg_name: Optional[str] = None,
                 **kwargs) -> None:
        self.operation = operation
        self.parent_scope = parent_scope
        self.arg_names = arg_names
        self.var_arg_name = var_arg_name
        self.bound_object = kwargs.get("bound_object", None)
        super().__init__(function_class)


def function_copy(this: Function):
    return Function(this.operation,
                    this.parent_scope,
                    this.arg_names,
                    this.var_arg_name)


def function_call(this: Function, args: List[Object]):
    return FunctionCall(this, [Constant(arg) for arg in args]).eval(())


class FunctionCreate(IComputable):
    def __init__(self,
                 operation: Type[IComputable],
                 arg_names: Iterable[str],
                 var_arg_name: Optional[str] = None):
        self.operation = operation
        self.arg_names = arg_names
        self.var_arg_name = var_arg_name

    def eval(self, scope_path: tuple) -> Function:
        return Function(self.operation,
                        scope_path,
                        self.arg_names,
                        self.var_arg_name)


def create_locals(func, args):  # TODO: Add parent variable
    unpacked_args = []
    for obj in args:
        if type(obj) is list:
            unpacked_args.extend(obj)
        else:
            unpacked_args.append(obj)
    new_locals = {name: arg for name, arg in zip(func.arg_names, unpacked_args)}
    if func.var_arg_name is not None:
        new_locals[func.var_arg_name] = forward_declarations["array"](unpacked_args[len(func.arg_names):])
    if func.bound_object is not None:
        new_locals["this"] = func.bound_object
    return new_locals


class FunctionCall(IComputable):
    def __init__(self,
                 function: Type[IComputable],
                 arguments: Iterable[IComputable]) -> None:
        self.function = function
        self.arguments = arguments

    def eval(self, scope_path: tuple) -> Type[Object]:
        f = self.function.eval(scope_path)
        if type(f) is not Function:
            f = f.attributes["#call"]
        assert(len(f.arg_names) <= len(self.arguments))

        new_locals = create_locals(f, [arg.eval(scope_path) for arg in self.arguments])
        with CreateScope(f.parent_scope, new_locals) as new_path:
            result = f.operation.eval(new_path)
            result.is_return = False
            return result


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
                position = i

    return (best_method, position)


class OperatorCall(IComputable):
    def __init__(self, name: str, arguments: Iterable[Type[IComputable]]) -> None:
        self.name = name
        self.arguments = arguments

    def eval(self, scope_path: tuple) -> Type[Object]:
        obj_list = [arg.eval(scope_path) for arg in self.arguments]
        objs = []
        for obj in obj_list:
            if type(obj) is list:
                objs.extend(obj)
            else:
                objs.append(obj)

        method, position = resolve_overload(self.name, objs)

        if method is None:
            raise f"Cant perform {self.name} on objects of types\
                    {', '.join([str(obj.type) for obj in objs])}"

        del objs[position]

        new_locals = create_locals(method, objs)

        with CreateScope(method.parent_scope, new_locals) as new_path:
            result = method.operation.eval(new_path)
            result.is_return = False
            return result


class NoneType(IPrimitiveType):
    def __init__(self) -> None:
        super().__init__(none_class)


def none_to_string(this):
    return forward_declarations["string"]("none")


def none_to_bool(this):
    return forward_declarations["bool"](False)


def none_to_int(this):
    return forward_declarations["int"](0)


def none_to_float(this):
    return forward_declarations["float"](0.0)


class UnpackOperation(IComputable):
    def __init__(self, value: Type[IComputable]) -> None:
        self.value = value

    def eval(self, scope_path: tuple) -> List[Type[Object]]:
        return unpack(self.value.eval(scope_path))


def unpack(obj: Type[Object]) -> List[Type[Object]]:
    return list(obj)


def register_primitive(name: str, cls, type: Class) -> None:
    Variable.table[(name,)] = type
    forward_declarations[name] = cls


class_class = Class("class", {})
function_class = Class("function", {})


class_class.methods["constructor"] = to_primitive_function(class_constructor)
Object.__init__(class_class, class_class)


none_class = Class("NoneType", {})
none_object = NoneType()


register_primitive("class", Class, class_class)
register_primitive("function", Function, function_class)
register_primitive("NoneType", NoneType, none_class)

Assignment(Variable("none"), Constant(none_object)).eval(())
