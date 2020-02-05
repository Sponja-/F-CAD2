from .base import IPrimitiveType, Class
from .numerical import Int


class String(IPrimitiveType):
    def __init__(self, value: str):
        self.value = value
        super().__init__(string_class)


def string_get_item(this: String, index: Int) -> String:
    assert(type(index) is Int)
    return String(this.value[index.value])


def string_set_item(this: String, index: Int, value: String) -> String:
    assert(type(index) is Int)
    assert(len(value.value) == 1)
    this.value[index.value] = value.value
    return value


def string_del_item(this: String, index: Int) -> String:
    assert(type(index) is Int)
    result = String(this.value[index.value])
    del this.value[index.value]
    return result


def string_combine(this: String, other: String) -> String:
    return String(this.value + other.value)


string_class = Class("string", {

}, {})