from .base import Class, IPrimitiveType, Object, forward_declarations
from .base import NoneType, to_primitive_function, register_class
from .base import OperatorCall, Constant, MemberCall, IComputable
from .base import UnpackOperation, Variable, ConstructorCall
from .base import IAssignable
from .logic import Bool
from .numerical import Int
from .exceptions import raise_stop_iter
from .flow_control import ListComprehensionConstant
from typing import List, Type, Dict


class Tuple(IPrimitiveType):
    def __init__(self, elements=()) -> None:
        self.elements = tuple(elements)
        self.iter_current = 0
        super().__init__(tuple_class)


def tuple_constructor(this: Tuple, *args: Type[Object]):
    this.elements = tuple(args)


def tuple_get_item(this: Tuple, index: Int) -> Type[Object]:
    assert(type(index) is Int)
    return this.elements[index.value]


def tuple_combine(this: Tuple, other: Tuple) -> Tuple:
    return Tuple(this.elements + other.elements)


def tuple_length(this: Tuple) -> Int:
    return Int(len(this.elements))


def tuple_equal(this: Tuple, other: Tuple) -> Bool:
    if len(this.elements) != len(other.elements):
        return Bool(False)
    return Bool(all(OperatorCall("#equal", [Constant(elem1), Constant(elem2)]).eval(()).value
                for elem1, elem2 in zip(this.elements, other.elements)))


def tuple_not_equal(this: Tuple, other: Tuple) -> Bool:
    if len(this.elements) != len(other.elements):
        return Bool(True)
    return Bool(any(not(OperatorCall("#equal", [Constant(elem1), Constant(elem2)]).eval(()).value)
                    for elem1, elem2 in zip(this.elements, other.elements)))


def tuple_hash(this: Tuple) -> Int:
    return Int(hash(this.elements))


def tuple_to_bool(this: Tuple) -> Bool:
    return Bool(bool(len(this.elements)))


def tuple_iter(this: Tuple) -> Tuple:
    this.iter_current = 0
    return this


def tuple_next(this: Tuple) -> Type[Object]:
    if this.iter_current < len(this.elements):
        result = this.elements[this.iter_current]
        this.iter_current += 1
        return result
    else:
        return raise_stop_iter()


def tuple_to_string(this: Tuple):
    return forward_declarations["string"](repr(this.elements))


def static_tuple_call(this: Class, arg: Type[Object]) -> Tuple:
    return Tuple(tuple(arg))


tuple_class = Class("tuple", {
    "constructor":      to_primitive_function(tuple_constructor),
    "#get_item":        to_primitive_function(tuple_get_item),
    "#append_left":     to_primitive_function(tuple_combine),
    "length":           to_primitive_function(tuple_length),
    "#equal":           to_primitive_function(tuple_equal),
    "#not_equal":       to_primitive_function(tuple_not_equal),
    "#hash":            to_primitive_function(tuple_hash),
    "#to_bool":         to_primitive_function(tuple_to_bool),
    "#iter":            to_primitive_function(tuple_iter),
    "#next":            to_primitive_function(tuple_next),
    "#to_string":       to_primitive_function(tuple_to_string)
}, {
    "#call":            to_primitive_function(static_tuple_call)
})


class Array(IPrimitiveType):
    def __init__(self, elements: List[Type[Object]] = []) -> None:
        self.elements = list(elements)
        self.iter_current = 0
        super().__init__(array_class)


def array_constructor(this: Array, *args):
    this.elements = list(args)


def array_get_item(this: Array, index: Int) -> Object:
    assert(type(index) is Int)
    return this.elements[index.value]


def array_set_item(this: Array, index: Int, value: Type[Object]) -> Type[Object]:
    assert(type(index) is Int)
    this.elements[index.value] = value
    return value


def array_del_item(this: Array, index: Int) -> Type[Object]:
    assert(type(index) is Int)
    value = this.elements[index.value]
    del this.elements[index.value]
    return value


def array_combine(this: Array, other: Array) -> Array:
    return Array(this.elements + other.elements)


def array_length(this: Array):
    return Int(len(this.elements))


def array_add(this: Array, value: Type[Object]) -> NoneType:
    this.elements.append(value)
    return this


def array_insert(this: Array, index: Int, value: Type[Object]) -> NoneType:
    assert(type(index) is Int)
    this.elements.insert(index, value)
    return this


def array_equal(this: Array, other: Array) -> Bool:  # TODO
    if len(this.elements) != len(other.elements):
        return Bool(False)
    return Bool(all(OperatorCall("#equal", [Constant(elem1), Constant(elem2)]).eval(()).value
                for elem1, elem2 in zip(this.elements, other.elements)))


def array_not_equal(this: Tuple, other: Tuple) -> Bool:
    if len(this.elements) != len(other.elements):
        return Bool(True)
    return Bool(any(not(OperatorCall("#equal", [Constant(elem1), Constant(elem2)]).eval(()).value)
                    for elem1, elem2 in zip(this.elements, other.elements)))


def array_to_bool(this: Array) -> Bool:
    return Bool(bool(len(this.elements)))


def array_iter(this: Array) -> Array:
    this.iter_current = 0
    return this


def array_next(this: Array) -> Array:
    if this.iter_current < len(this.elements):
        result = this.elements[this.iter_current]
        this.iter_current += 1
        return result
    else:
        return raise_stop_iter()


def array_to_string(this: Array):
    return forward_declarations["string"](repr(this.elements))


def static_array_call(this: Class, arg: Type[Object]) -> Array:
    return Array(list(arg))


array_class = Class("array", {
    "constructor":      to_primitive_function(array_constructor),
    "#get_item":        to_primitive_function(array_get_item),
    "#set_item":        to_primitive_function(array_set_item),
    "#del_item":        to_primitive_function(array_del_item),
    "#append_left":     to_primitive_function(array_combine),
    "length":           to_primitive_function(array_length),
    "insert":           to_primitive_function(array_insert),
    "add":              to_primitive_function(array_add),
    "#equal":           to_primitive_function(array_equal),
    "#not_equal":       to_primitive_function(array_not_equal),
    "#to_bool":         to_primitive_function(array_to_bool),
    "#iter":            to_primitive_function(array_iter),
    "#next":            to_primitive_function(array_next),
    "#to_string":       to_primitive_function(array_to_string)
}, {
    "#call":            to_primitive_function(static_array_call)
})


class Dictionary(IPrimitiveType):
    def __init__(self, elements: Dict[Type[Object], Type[Object]] = {}):
        self.elements = elements
        super().__init__(dictionary_class)


def dict_constructor(this: Dictionary, arg: Type[Object]) -> None:
    if arg.type.name == "dictionary":
        this.elements = arg.elements
    elif "#iter" in arg:
        result = {}
        for value in arg:
            pair = []
            for x in value:
                pair.append(x)
            assert(len(pair) == 2)
            result[pair[0]] = pair[1]
        this.elements = result


def dict_get_item(this: Dictionary, index: Type[Object]) -> Type[Object]:
    return this.elements[index]


def dict_set_item(this: Dictionary, index: Type[Object], value: Type[Object]) -> Type[Object]:
    this.elements[index] = value
    return value


def dict_del_item(this: Dictionary, index: Type[Object]) -> Type[Object]:
    value = this.elements[index]
    del this.elements[index]
    return value


def dict_combine(this: Dictionary, other: Dictionary) -> Dictionary:
    return Dictionary({**this.elements, **other.elements})


def dict_update(this: Dictionary, other: Dictionary) -> Dictionary:
    this.elements.update(other.elements)
    return this


def dict_keys(this: Dictionary) -> Tuple:
    return Tuple(this.elements.keys())


def dict_values(this: Dictionary) -> Tuple:
    return Tuple(this.elements.values())


def dict_items(this: Dictionary) -> Tuple:
    return Tuple((Tuple(pair) for pair in zip(this.elements.keys(), this.elements.values())))


def dict_iter(this: Dictionary) -> Tuple:
    keys = this.call("keys")
    return keys.call("#iter")


def dict_to_string(this: Dictionary):
    return forward_declarations["string"](repr(this.elements))


def dict_length(this: Dictionary):
    return Int(len(this.elements))


def dict_to_bool(this: Dictionary) -> Bool:
    return Bool(bool(len(this.elements)))


def static_dict_call(this: Class, arg: Type[Object]) -> Object:
    result = {}
    for value in arg:
        pair = []
        for x in value:
            pair.append(x)
        assert(len(pair) == 2)
        result[pair[0]] = pair[1]
    return result


dictionary_class = Class("dict", {
    "constructor":      to_primitive_function(dict_constructor),
    "#get_item":        to_primitive_function(dict_get_item),
    "#set_item":        to_primitive_function(dict_set_item),
    "#del_item":        to_primitive_function(dict_del_item),
    "#append_left":     to_primitive_function(dict_combine),
    "update":           to_primitive_function(dict_update),
    "keys":             to_primitive_function(dict_keys),
    "values":           to_primitive_function(dict_values),
    "items":            to_primitive_function(dict_items),
    "#iter":            to_primitive_function(dict_iter),
    "#to_string":       to_primitive_function(dict_to_string)
}, {
    "#call":            to_primitive_function(static_dict_call)
})


register_class("tuple", Tuple, tuple_class)
register_class("array", Array, array_class)
register_class("dict", Dictionary, dictionary_class)


class ItemAccess(IComputable, IAssignable):
    def __init__(self,
                 iterable: Type[IComputable],
                 arguments: Type[IComputable]):
        self.iterable = iterable
        self.arguments = arguments

    def eval(self, scope_path: tuple) -> Type[Object]:
        return MemberCall(self.iterable, "#get_item", self.arguments).eval(scope_path)

    def set_value(self, scope_path: tuple, value: Type[Object]) -> Type[Object]:
        return MemberCall(self.iterable, "#set_item", self.arguments + [Constant(value)]).eval(scope_path)


class ArrayConstant(IComputable, IAssignable):
    def __init__(self,
                 arguments: List[Type[IComputable]]) -> None:
        self.arguments = arguments

    def eval(self, scope_path: tuple) -> Type[Object]:
        if len(self.arguments) == 1 and isinstance(self.arguments[0], ListComprehensionConstant):
            return Variable("array").eval(()).call("#call", self.arguments[0].eval(scope_path))
        return ConstructorCall(Variable("array"), self.arguments).eval(scope_path)

    def set_value(self, scope_path: tuple, value) -> Type[Object]:
        iterator = iter(value)
        for arg in self.arguments[:-1]:
            arg.set_value(scope_path, next(iterator))
        if isinstance(self.arguments[-1], UnpackOperation):
            self.arguments[-1].value.set_value(scope_path, Tuple(iterator))
        else:
            self.arguments[-1].set_value(scope_path, next(iterator))


class TupleConstant(IComputable):
    def __init__(self,
                 arguments: List[Type[IComputable]]) -> None:
        self.arguments = arguments

    def eval(self, scope_path: tuple) -> Type[Object]:
        if len(self.arguments) == 1 and isinstance(self.arguments[0], ListComprehensionConstant):
            return Variable("tuple").call("#call", self.arguments[0].eval(scope_path))
        return ConstructorCall(Variable("tuple"), self.arguments).eval(scope_path)


class DictionaryConstant(IComputable):
    def __init__(self, lines: List) -> None:
        self.lines = lines

    def eval(self, scope_path: tuple) -> Type[Object]:
        result_elems = {}
        for line in self.lines:
            if len(line) == 2:
                result_elems[line[0].eval(scope_path)] = line[1].eval(scope_path)
            else:
                assert(isinstance(line[0], UnpackOperation))
                result_elems.update(line[0].value.eval(scope_path).elements)
        return Dictionary(result_elems)
