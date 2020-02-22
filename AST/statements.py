from .base import IComputable, Object, create_none
from typing import Type, Iterable


class IStatement(IComputable):
    pass


class ReturnStatement(IStatement):
    def __init__(self, value: Type[IComputable]):
        self.value = value

    def eval(self, scope_path: tuple) -> Type[Object]:
        result = self.value.eval(scope_path)
        result.is_return = True
        return result


class ExprStatement(IStatement):
    def __init__(self, expression: Type[IComputable]):
        self.expression = expression

    def eval(self, scope_path: tuple) -> Type[Object]:
        return self.expression.eval(scope_path)


class StatementList(IStatement):
    def __init__(self,
                 statements: Iterable[Type[IStatement]]) -> None:
        self.statements = statements

    def eval(self, scope_path: tuple) -> Type[Object]:
        ret_val = create_none()
        for statement in self.statements:
            result = statement.eval(scope_path)
            if result.is_return or result.is_except:
                ret_val = result
                break
        return ret_val
