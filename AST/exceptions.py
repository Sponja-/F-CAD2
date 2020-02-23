from .base import Object, IComputable, IPrimitiveType, Class, ConstructorCall
from .base import Variable, create_none, register_class, Constant
from .statements import StatementList
from typing import Type, Optional


class RaiseStatement(IComputable):
    def __init__(self, value: IComputable) -> None:
        self.value = value

    def eval(self, scope_path: tuple) -> Type[Object]:
        result = self.value.eval(scope_path)
        result.is_except = True
        return result


class TryCatch(IComputable):
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
            catch_result = self.catch_body.eval(scope_path)
        if result.finally_body is not None:
            finally_result = self.finally_body.eval(scope_path)
        return (catch_result or finally_result) or create_none()


class StopIteration(IPrimitiveType):
    def __init__(self):
        super().__init__(StopIteration_class)


StopIteration_class = Class("StopIteration", {}, {})


def raise_stop_iter():
    return RaiseStatement(ConstructorCall(Constant(StopIteration_class), [])).eval(())


register_class("StopIteration", StopIteration, StopIteration_class)
