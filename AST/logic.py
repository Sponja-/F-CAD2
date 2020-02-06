from .base import Class, IPrimitiveType, forward_declarations, Object
from .base import IComputable, to_primitive_function, register_primitive
from typing import Type


class Bool(IPrimitiveType):
    def __init__(self, value: bool = False) -> None:
        self.value = value
        super().__init__(bool_class)


def try_bool(obj: Type[Object]):
    if type(obj) is Bool:
        return obj
    if obj.type.has_method("#to_bool"):
        return obj.call("#to_bool")
    raise f"Could not convert {obj} to bool"


class AndOperation(IComputable):
    def __init__(self, left: IComputable, right: IComputable) -> None:
        self.left = left
        self.right = right

    def eval(self, scope_path: tuple) -> Type[Object]:
        left_obj = self.left.eval(scope_path)
        left_bool = try_bool(left_obj)
        if not left_bool.value:
            return left_obj
        return self.right.eval(scope_path)


class OrOperation(IComputable):
    def __init__(self, left: IComputable, right: IComputable) -> None:
        self.left = left
        self.right = right

    def eval(self, scope_path: tuple) -> Type[Object]:
        left_obj = self.left.eval(scope_path)
        left_bool = try_bool(left_obj)
        if left_bool.value:
            return left_obj
        return self.right.eval(scope_path)


class NotOperation(IComputable):
    def __init__(self, value: IComputable) -> None:
        self.value = value

    def eval(self, scope_path: tuple) -> Type[Object]:
        obj = self.value.eval(scope_path)
        return Bool(not try_bool(obj).value)


def bool_equal(this: Bool, other: Bool) -> Bool:
    return Bool(this.value == other.value)


def bool_not_equal(this: Bool, other: Bool) -> Bool:
    return Bool(this.value != other.value)


def bool_hash(this: Bool):
    return forward_declarations["int"](hash(this.value))


def bool_to_string(this: Bool):
    return forward_declarations["string"]("true" if this.value else "false")


def bool_to_int(this: Bool):
    return forward_declarations["int"](int(this.value))


bool_class = Class("bool", {
    "#equal":       to_primitive_function(bool_equal),
    "#not_equal":   to_primitive_function(bool_not_equal),
    "#hash":        to_primitive_function(bool_hash),
    "#to_string":   to_primitive_function(bool_to_string),
    "#to_int":      to_primitive_function(bool_to_int)
}, {})


register_primitive("bool", Bool, bool_class)
