from .base import Object, IComputable, IPrimitiveType, Class, to_primitive_function
from .base import Variable, none_object, register_primitive
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
            Variable(self.except_name).set_value(scope_path, result)
            catch_result = self.catch_body.exec(scope_path)
        if result.finally_body is not None:
            finally_result = self.finally_body.exec(scope_path)
        return (catch_result or finally_result) or none_object


class StopIteration(IPrimitiveType):
    def __init__(self):
        super().__init__(StopIteration_class)


def StopIteration_constructor(this):
    pass


StopIteration_class = Class("StopIteration", {
    "constructor":     to_primitive_function(StopIteration_constructor)
}, {})


register_primitive("StopIteration", StopIteration, StopIteration_class)
