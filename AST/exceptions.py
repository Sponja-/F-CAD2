from .base import Object, IComputable, IPrimitiveType, none_class
from .base import forward_declarations, CreatePath, none_object
from .statements import IStatement, StatementList
from typing import Type, Optional


class Raise(IStatement):
    def __init__(self, value: IComputable) -> None:
        self.value = value

    def eval(self, scope_path: tuple) -> Type[Object]:
        result = self.value.eval(scope_path)
        result.is_except = True
        return result


class TryCatch(IStatement):
    def __init__(self,
                 try_body: StatementList,
                 except_name: str,
                 catch_body: StatementList,
                 finally_body: Optional[StatementList]) -> None:
        self.try_body = try_body
        self.except_name = except_name
        self.catch_body = catch_body
        self.finally_body = finally_body

    def eval(self, scope_path: tuple) -> Type[Object]:
        result = self.try_body.eval(scope_path)
        catch_result = None
        finally_result = None
        if result.is_except:
            result.is_except = False
            with CreatePath(scope_path, {self.except_name: result}) as new_path:
                catch_result = self.catch_body.eval(new_path)
        if result.finally_body is not None:
            finally_result = self.finally_body.eval(scope_path)
        return (catch_result or finally_result) or none_object


class StopIteration(IPrimitiveType):
    def __init__(self):
        super().__init__(none_class)


forward_declarations["StopIteration"] = StopIteration
