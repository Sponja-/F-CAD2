from typing import Dict, Iterable, Optional, Callable, List, Type, Union
from abc import ABC, abstractmethod
from inspect import getfullargspec
from functools import wraps

forward_declarations = {}
class_class_created = False

LocalsType = Dict[str, Union[Type["Object"], Type["IComputable"], str]]


class Object(Exception):
    def __init__(self, type: "Class") -> None:
        self.type = type
        self.attributes = {}
        self.is_return = False

    def call(self, name: str, *args: List[Type["Object"]]) -> Type["Object"]:
        return MemberCall(Constant(self), name, [Constant(arg) for arg in args]).eval(())

    def get(self, index):
        return self.attributes.get(index, self.type.get_method(index))

    def set(self, index, value):
        self.attributes[index] = value

    def has(self, index):
        return index in self.attributes or self.type.has_method(index)

    def __hash__(self):
        return self.call("#hash").value

    def __repr__(self):
        if self.has("#to_string"):
            return self.call("#to_string").value
        else:
            return f"instance of {self.type.name}"

    def __iter__(self):
        return self.call("#iter")

    def __next__(self):
        try:
            result = self.call("#next")
        except Exception as e:
            if isinstance(e, Object) and e.type.name == "StopIteration":
                raise StopIteration
            else:
                raise e
        return result


class IComputable(ABC):
    @abstractmethod
    def eval(self, scope_path: tuple) -> Type[Object]:
        pass


class IAssignable(ABC):
    @abstractmethod
    def set_value(self, scope_path: tuple, value: Type[Object]) -> None:
        pass


class Call(IComputable):
    @staticmethod
    def do_call(function: "Function",
                new_locals: Dict[str, Object]):
        with CreateScope(function.parent_scope, new_locals) as new_scope:
            result = function.operation.eval(new_scope)
            result.is_return = False
            result.is_yield = False
            return result


class Constant(IComputable):
    def __init__(self, value: Type[Object]) -> None:
        self.value = value

    def eval(self, scope_path: tuple) -> Type[Object]:
        return self.value


class Scope:
    scope_n = 0

    def __init__(self,
                 elements: LocalsType = {}):
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

    def names(self):
        return list(self.elements.keys())

    def new_scope(self,
                  path: tuple,
                  elements: LocalsType) -> tuple:
        if len(path) > 0:
            return (path[0],) + self.elements[path[0]].new_scope(path[1:], elements)
        else:
            result = Scope.scope_n
            Scope.scope_n += 1
            self.elements[result] = Scope(elements)
            return (result,)


class CreateScope:
    def __init__(self, path: tuple, elements: LocalsType, *, persistent=True) -> None:
        self.path = path
        self.elements = elements
        self.persistent = persistent

    def __enter__(self):
        self.new_path = Variable.table.new_scope(self.path, self.elements)
        return self.new_path

    def __exit__(self, type, value, traceback):
        if not self.persistent:
            del Variable.table[self.new_path]


class Variable(IComputable, IAssignable):
    table = Scope()

    def __init__(self, name: str) -> None:
        self.name = name

    def eval(self, scope_path: tuple) -> Type[Object]:
        result = Variable.table[scope_path + (self.name,)]
        if result is not None:
            return result
        raise IndexError(f"Name {self.name} could not be resolved")

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
        return create_none()


class IPrimitiveType(Object):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PrimitiveCall(IComputable):
    def __init__(self,
                 function: Callable[[tuple], Type[Object]]) -> None:
        self.function = function

    def eval(self, scope_path: tuple) -> Type[Object]:
        value = self.function(scope_path)
        if value is None:
            return create_none()
        else:
            return value


def to_primitive_function(func: Callable) -> "Function":
    specs = getfullargspec(func)

    arg_names = specs[0]
    var_arg_name = specs[1]
    has_kw_arg = specs[2] is not None

    @wraps(func)
    def primitive_func(scope_path: tuple):
        if has_kw_arg:
            kwargs = {key.value: value for key, value in Variable("#kwargs").eval(scope_path).elements.items()}
            if var_arg_name is None:
                return func(*[Variable(name).eval(scope_path) for name in arg_names], **kwargs)
            else:
                return func(*[Variable(name).eval(scope_path) for name in arg_names],
                            *Variable(var_arg_name).eval(scope_path).elements, **kwargs)
        else:
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
                 parent_scope: tuple = (),
                 parent: Optional["Class"] = None) -> None:
        self.name = name
        self.methods = methods
        self.parent = parent
        self.parent_scope = parent_scope
        if self.name != "ClassType":
            super().__init__(class_class)
            self.attributes.update(statics)

    def has_method(self, index: str) -> bool:
        return (index in self.methods or
                (self.parent is not None and self.parent.has_method(index)))

    def get_method(self, index: str) -> "Function":
        return self.methods.get(index, self.parent.get_method(index) if self.parent is not None else None)

    def __str__(self):
        return self.name


class ClassCreate(IComputable):
    def __init__(self,
                 name: str,
                 methods: Dict[str, Type[IComputable]],
                 statics: Dict[str, Type[IComputable]],
                 parent_name: Optional[str] = None) -> None:
        self.name = name
        self.methods = methods
        self.statics = statics
        self.parent_name = parent_name

    def eval(self, scope_path: tuple) -> Class:
        return Class(self.name,
                     {name: value.eval(scope_path) for name, value in self.methods.items()},
                     {name: value.eval(scope_path) for name, value in self.statics.items()},
                     scope_path,
                     self.parent_name)


def class_equal(this: Class, other: Class):
    return forward_declarations["Bool"](this.name == other.name)


def class_not_equal(this: Class, other: Class):
    return forward_declarations["Bool"](this.name != other.name)


class ConstructorCall(Call):
    def __init__(self,
                 type: IComputable,
                 args: Iterable[IComputable],
                 kwargs=None) -> None:
        self.type = type
        self.args = args
        self.kwargs = Constant(NoneType()) if kwargs is None else kwargs

    def eval(self, scope_path: tuple) -> Type[Object]:
        t = self.type.eval(scope_path)
        if t.name in forward_declarations:
            new_obj = forward_declarations[t.name]()
        else:
            new_obj = Object(t)

        if new_obj.has("constructor"):
            constructor = new_obj.get("constructor")
            new_locals = create_locals(constructor,
                                       [arg.eval(scope_path) for arg in self.args],
                                       self.kwargs.eval(scope_path), object=new_obj)
            Call.do_call(constructor, new_locals)
        return new_obj


class MemberAccess(IComputable, IAssignable):
    def __init__(self, object: Type[IComputable], name: str) -> None:
        self.object = object
        self.name = name

    def eval(self, scope_path: tuple) -> Type[Object]:
        obj = self.object.eval(scope_path)
        return obj.get(self.name)

    def set_value(self, scope_path: tuple, value: Object) -> None:
        self.object.eval(scope_path).set(self.name, value)


class MemberCall(Call):
    def __init__(self,
                 object: Type[IComputable],
                 name: str,
                 args: Iterable[IComputable],
                 kwargs=None):
        self.object = object
        self.name = name
        self.args = args
        self.kwargs = Constant(NoneType()) if kwargs is None else kwargs

    def eval(self, scope_path: tuple) -> Type[Object]:
        obj = self.object.eval(scope_path)
        f = obj.get(self.name)
        func = f

        if f is None:
            raise IndexError

        if type(f) is not Function:
            func = f.get("#call")
            new_locals = create_locals(func,
                                       [arg.eval(scope_path) for arg in self.args],
                                       self.kwargs.eval(scope_path), object=f)
        else:
            new_locals = create_locals(func, [arg.eval(scope_path) for arg in self.args],
                                       self.kwargs.eval(scope_path), object=obj)

        return Call.do_call(func, new_locals)


class Destructuring(IAssignable):
    def __init__(self, names: List[str]):
        self.names = names

    def set_value(self, scope_path: tuple, value: Type[Object]):
        for name in self.names:
            Variable(name).set_value(scope_path, value.get(name))


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
        self.default_args = kwargs.get("default_args", [])
        self.bound_object = kwargs.get("bound", None)
        super().__init__(function_class)


class FunctionCreate(IComputable):
    def __init__(self,
                 operation: Type[IComputable],
                 arg_names: Iterable[str],
                 var_arg_name: Optional[str] = None,
                 **kwargs):
        self.operation = operation
        self.arg_names = arg_names
        self.var_arg_name = var_arg_name
        self.default_args = kwargs.get("default_args", [])

    def eval(self, scope_path: tuple) -> Function:
        return Function(self.operation,
                        scope_path,
                        self.arg_names,
                        self.var_arg_name,
                        default_args=[default_arg.eval(scope_path)
                                      for default_arg in self.default_args])


def create_locals(func: Function,
                  args: List[Union[Type[Object], List[Type[Object]], Dict]],
                  kwargs: Dict[str, Type[Object]],
                  **options) -> LocalsType:  # TODO: Add parent variable
    unpacked_args = []
    for obj in args:
        if type(obj) is list:
            unpacked_args.extend(obj)
        elif type(obj) is dict:
            kwargs.update(obj)
        else:
            unpacked_args.append(obj)
    new_locals = {name: arg for name, arg in zip(func.arg_names, unpacked_args)}
    if len(func.arg_names) > len(unpacked_args):
        assert(len(func.default_args) + len(unpacked_args) >= len(func.arg_names))
        new_locals.update({name: arg for name, arg in
                           zip(reversed(func.arg_names),
                               func.default_args[:len(func.arg_names) - len(unpacked_args)])})
    if func.var_arg_name is not None:
        new_locals[func.var_arg_name] = forward_declarations["array"](unpacked_args[len(func.arg_names):])
    new_locals["this"] = (func.bound_object
                          if func.bound_object is not None
                          else options.get("object", create_none()))
    new_locals["#kwargs"] = forward_declarations["dict"](kwargs)
    return new_locals


class FunctionCall(Call):
    def __init__(self,
                 function: Type[IComputable],
                 args: Iterable[IComputable],
                 kwargs=None) -> None:
        self.function = function
        self.args = args
        self.kwargs = Constant(NoneType()) if kwargs is None else kwargs

    def eval(self, scope_path: tuple) -> Type[Object]:
        f = self.function.eval(scope_path)
        func = f
        if type(f) is not Function:
            func = f.get("#call")
            new_locals = create_locals(func,
                                       [arg.eval(scope_path) for arg in self.args],
                                       self.kwargs.eval(scope_path), object=f)
        else:
            new_locals = create_locals(func, [arg.eval(scope_path) for arg in self.args],
                                       self.kwargs.eval(scope_path))

        return Call.do_call(func, new_locals)


def best_fitting_method(operator_name, obj, pos, length):
    if obj.has(operator_name + f"_{str(pos)}"):
        return (obj.get(operator_name + f"_{str(pos)}"), True)
    elif pos == 0 and length == 2 and obj.has(operator_name + "_left"):
        return (obj.get(operator_name + "_left"), True)
    elif pos == 1 and length == 2 and obj.has(operator_name + "_right"):
        return (obj.get(operator_name + "_right"), True)

    if obj.has(operator_name):
        return (obj.get(operator_name), False)

    return (None, False)


def resolve_overload(operator_name, objects):
    best_method = None
    position = 0
    owner = None
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
                if with_pos:
                    has_pos = True
                if not primitive:
                    is_prim = False
                best_method = method
                position = i
                owner = obj

    return (best_method, position, owner)


class OperatorCall(Call):
    def __init__(self, name: str, arguments: Iterable[Type[IComputable]]) -> None:
        self.name = name
        self.arguments = arguments

    def eval(self, scope_path: tuple) -> Type[Object]:
        objs = [arg.eval(scope_path) for arg in self.arguments]

        f, position, owner = resolve_overload(self.name, objs)
        if f is None:
            raise f"Cant perform {self.name} on objects of types\
                    {', '.join([str(obj.type) for obj in objs])}"

        del objs[position]

        new_locals = create_locals(f, objs, forward_declarations["dict"]({}), object=owner)

        return Call.do_call(f, new_locals)


class NoneType(IPrimitiveType):
    def __init__(self) -> None:
        super().__init__(none_class)


def none_to_string(this):
    return forward_declarations["string"]("null")


def none_to_bool(this):
    return forward_declarations["bool"](False)


def none_to_int(this):
    return forward_declarations["int"](0)


def none_to_float(this):
    return forward_declarations["float"](0.0)


def create_none():
    return ConstructorCall(Variable("NoneType"), []).eval(())


class UnpackOperation(IComputable):
    def __init__(self, value: Type[IComputable]) -> None:
        self.value = value

    def eval(self, scope_path: tuple) -> List[Type[Object]]:
        return unpack(self.value.eval(scope_path))


def unpack(obj: Type[Object]):
    if isinstance(obj, forward_declarations["dict"]):
        return obj.elements
    else:
        return list(obj)


def register_class(name: str, cls, type: Class) -> None:
    Variable.table[(name,)] = type
    forward_declarations[name] = cls


def register_function(name, func):
    Variable.table[(name,)] = func


class_class = Class("ClassType", {})
function_class = Class("FunctionType", {})

class_class.methods["#equal"] = to_primitive_function(class_equal)
class_class.methods["#not_equal"] = to_primitive_function(class_not_equal)
Object.__init__(class_class, class_class)


none_class = Class("NoneType", {
    "#to_string":   to_primitive_function(none_to_string),
    "#to_bool":     to_primitive_function(none_to_bool),
    "#to_int":      to_primitive_function(none_to_int),
    "#to_float":    to_primitive_function(none_to_float)
})


register_class("ClassType", Class, class_class)
register_class("FunctionType", Function, function_class)
register_class("NoneType", NoneType, none_class)
