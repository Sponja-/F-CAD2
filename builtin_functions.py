from AST.base import register_function, to_primitive_function


def register_builtin(f):
    name = '_'.join(f.__name__.split('_')[:-1])
    register_function(name, to_primitive_function(f))
    return f


@register_builtin
def type_function(object):
    return object.type


@register_builtin
def iter_function(iterable):
    return iterable.call("#iter")


@register_builtin
def next_function(iterable):
    return iterable.call("#next")


@register_builtin
def print_function(*values):
    print(*[repr(value) for value in values])
