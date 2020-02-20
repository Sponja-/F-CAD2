from .base import IComputable, Object, create_none, FunctionCall, Constant
from .base import unpack, Variable, IAssignable, OperatorCall, forward_declarations
from .statements import StatementList, IStatement
from .logic import try_bool, Bool
from typing import Type, Optional, List


class ConditionalStatement(IStatement):
    def __init__(self,
                 condition: Type[IComputable],
                 if_body: StatementList,
                 else_body: Optional[StatementList] = None) -> None:
        self.condition = condition
        self.if_body = if_body
        self.else_body = else_body

    def eval(self, scope_path: tuple) -> Type[Object]:
        if try_bool(self.condition.eval(scope_path)).value:
            return self.if_body.eval(scope_path)
        elif self.else_body is not None:
            return self.else_body.eval(scope_path)


class ConditionalExpression(IComputable, IAssignable):
    def __init__(self,
                 condition: Type[IComputable],
                 if_expr: Optional[Type[IComputable]],
                 else_expr: Type[IComputable]) -> None:
        self.condition = condition
        self.if_expr = if_expr
        self.else_expr = else_expr

    def eval(self, scope_path: tuple) -> Type[Object]:
        condition = self.condition.eval(scope_path)
        if try_bool(condition).value:
            return (self.if_expr.eval(scope_path) if self.if_expr is not None else condition)
        else:
            return self.else_expr.eval(scope_path)

    def set_value(self, scope_path: tuple, value: Type[Object]):
        condition = self.condition.eval(scope_path)
        if try_bool(condition).value:
            if self.if_expr is not None:
                self.if_expr.set_value(scope_path, value)
            else:
                self.condition.set_value(scope_path)
        else:
            self.else_expr.set_vlaue(scope_path, value)


class BreakMarker:
    def __init__(self):
        self.is_return = True


class BreakStatement(IStatement):  # Needs to be returned
    def eval(self, scope_path: tuple) -> BreakMarker:
        return BreakMarker()


class ContinueMarker:
    def __init__(self):
        self.is_return = True


class ContinueStatement(IStatement):
    def eval(self, scope_path: tuple) -> ContinueMarker:
        return ContinueMarker()


class WhileStatement(IStatement):
    def __init__(self,
                 condition: Type[IComputable],
                 body: StatementList) -> None:
        self.condition = condition
        self.body = body

    def eval(self, scope_path: tuple) -> Type[Object]:
        while try_bool(self.condition.eval(scope_path)).value:
            result = self.body.eval(scope_path)
            if result is not None:
                if type(result) is BreakMarker:
                    break
                if type(result) is ContinueMarker:
                    continue
                if result.is_return or result.is_except:
                    return result
        return create_none()


class ForStatement(IStatement):
    def __init__(self,
                 iter_vars: List[str],
                 iterable: IComputable,
                 body: StatementList):
        self.iter_vars = iter_vars
        self.iterable = iterable
        self.body = body

    def eval(self, scope_path: tuple) -> Type[Object]:
        for value in self.iterable.eval(scope_path):
            values = [value]
            if len(self.iter_vars) > 1:
                values = unpack(value)
            for name, val in zip(self.iter_vars, values):
                Variable(name).set_value(scope_path, val)
            result = self.body.eval(scope_path)
            if result is not None:
                if type(result) is BreakMarker:
                    break
                if type(result) is ContinueMarker:
                    continue
                if result.is_return or result.is_except:
                    return result
        return create_none()


class ContainsOperation(IComputable):
    def __init__(self,
                 value: Type[IComputable],
                 iterable: Type[IComputable]) -> None:
        self.value = value
        self.iterable = iterable

    def eval(self, scope_path: tuple) -> Bool:
        iter = self.iterable.eval(scope_path)
        if "#contains" in iter:
            return Bool(try_bool(FunctionCall(iter["#contains"], [self.value]).eval(scope_path)).value)
        elif "#iter" in iter:
            val = self.value.eval(scope_path)
            iterator = iter.call("#iter")
            for elem in iterator:
                if OperatorCall("#equal", [Constant(elem), Constant(val)]).eval(()).value:
                    return Bool(True)
            return Bool(False)
        raise SyntaxError


class ListComprehension(IComputable):
    def __init__(self,
                 operation: Type[IComputable],
                 iter_vars: List[str],
                 iterable: Type[IComputable],
                 conditions: List[Type[IComputable]]):
        self.operation = operation
        self.iter_vars = iter_vars
        self.iterable = iterable
        self.conditions = conditions

    def eval(self, scope_path: tuple) -> Type[Object]:
        result = []
        for value in self.iterable.eval(scope_path):
            values = [value]
            if len(self.iter_vars) > 1:
                values = unpack(value)
            for name, val in zip(self.iter_vars, values):
                Variable(name).set_value(scope_path, val)
            if not all([try_bool(cond.eval(scope_path)) for cond in self.conditions]):
                continue
            result.append(self.operation.eval(scope_path))
        return forward_declarations["Tuple"](tuple(result))
