from .base import IComputable, Object, none_object
from typing import Type, Iterable


class IStatement(IComputable):
    def exec(self, scope_path: tuple):
        result = self.eval(scope_path)
        if result.is_return or result.is_except:
            return result
        return None


class Return(IStatement):
    def __init__(self, value: Type[IComputable]):
        self.value = value

    def eval(self, scope_path: tuple) -> Type[Object]:
        result = self.value.eval(scope_path)
        result.is_return = True
        return result


class ExprStatement(IComputable):
    def __init__(self, expression: Type[IComputable]):
        self.expression = expression

    def eval(self, scope_path: tuple) -> Type[Object]:
        return self.expression.eval(scope_path)


class StatementList(IComputable):
    def __init__(self,
                 statements: Iterable[Type[IStatement]],
                 scoped: bool = True) -> None:
        self.statements = statements
        self.scoped = scoped

    def eval(self, scope_path: tuple) -> Type[Object]:
        ret_val = none_object
        for statement in self.statements:
            result = statement.exec(scope_path)
            if result is not None:
                ret_val = result
                break
        return ret_val
