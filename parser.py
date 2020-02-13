from AST.base import ClassCreate, FunctionCreate, Assignment, Variable
from AST.base import IAssignable
from AST.statements import StatementList, Statement, ReturnStatement
from AST.exceptions import *
from AST.logic import *
from AST.flow_control import BreakStatement, ContinueStatement
from AST.flow_control import ConditionalStatement, WhileStatement, ForStatement
from AST.numerical import *
from AST.collection_types import *
from AST.string_type import *

from tokenizer import Tokenizer, TokenType


class Parser:
    def __init__(self, text):
        self.tokens = Tokenizer(text).get_token_list()
        self.pos = 0
        self.show_errors = True

    def error(self, message=""):
        if self.show_errors:
            print(f"Error on {self.token} at pos {self.pos}:\n\t{message}")
        raise SyntaxError

    @property
    def token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        self.pos -= 1
        self.error("Unexpected EOF")

    @property
    def next_token(self):
        if self.pos < len(self.tokens) - 1:
            return self.tokens[self.pos + 1]
        self.error("Unexpected EOF")

    @property
    def prev_token(self):
        if self.pos > 0:
            return self.tokens[self.pos - 1]
        self.error("Expected previous token")

    def eat(self, type, value=None):
        if self.token.type != type or (value is not None and self.token.value != value):
            self.error(f"Expected {type}" + (f"of value {value}" if value is not None else ""))
        else:
            value = self.token.value
            self.pos += 1
            return value

    def statement_block(self):
        if self.token.value != '{':
            return self.statement()
        self.eat(TokenType.GROUP)
        result = self.statement_list()
        self.eat(TokenType.GROUP, '}')
        return result

    def statement_list(self):
        s = self.statement()
        result = [s] if s is not None else []
        while self.token.value != '}' and self.token.type != TokenType.EOF:
            if self.prev_token.value != '}':
                self.eat(TokenType.SEMICOLON)
            s = self.statement()
            if s is not None:
                result.append(s)
        return StatementList(result)

    def statement(self):
        return self.special_statement()

    def special_statement(self):
        if self.token.value == "return":
            return ReturnStatement(self.expr_statement())
        if self.token.value == "break":
            self.eat(TokenType.KEYWORD)
            self.eat(TokenType.SEMICOLON)
            return BreakStatement()
        if self.token.value == "continue":
            self.eat(TokenType.KEYWORD)
            self.eat(TokenType.SEMICOLON)
            return ContinueStatement()
        return self.flow_statement()

    def flow_statement(self):
        if self.token.type == TokenType.KEYWORD:
            if self.token.value == "if":
                self.eat(TokenType.KEYWORD)
                self.eat(TokenType.GROUP, '(')
                condition = self.expr()
                self.eat(TokenType.GROUP, ')')
                body = self.statement_block()
                if self.token.value == "else":
                    self.eat(TokenType.KEYWORD)
                    else_body = self.statement_block()
                else:
                    else_body = None
                return ConditionalStatement(condition, body, else_body)
            if self.token.value == "while":
                self.eat(TokenType.KEYWORD)
                self.eat(TokenType.GROUP, '(')
                condition = self.expr()
                self.eat(TokenType.GROUP, ')')
                body = self.statement_block()
                return WhileStatement(condition, body)
            if self.token.value == "for":
                self.eat(TokenType.KEYWORD)
                self.eat(TokenType.GROUP, '(')
                names = [self.eat(TokenType.NAME)]
                while self.token.type == TokenType.COMMA:
                    self.eat(TokenType.COMMA)
                    names.append(self.eat(TokenType.NAME))
                self.eat(TokenType.KEYWORD, "in")
                iterable = self.expr()
                self.eat(TokenType.GROUP, ')')
                body = self.statement_block()
                return ForStatement(names, iterable, body)
        return self.expr_statement()

    def expr_statement(self):
        result = Statement(self.class_definition())
        self.eat(TokenType.SEMICOLON)
        return result

    def class_definition(self):
        if self.token.value == "class":
            self.eat(TokenType.KEYWORD)
            name = self.eat(TokenType.NAME)
            if self.token.value == "extends":
                self.eat("KEYWORD")
                parent_name = self.eat(TokenType.NAME)
            else:
                parent_name = None
            methods = {}
            statics = {}
            self.eat(TokenType.GROUP, '{')
            while self.token.value != '}' and self.token.type != TokenType.EOF:
                if self.token.value == "static":
                    self.eat(TokenType.KEYWORD)
                    definition = self.function_definition()
                    statics[definition.object.name] = definition.value
                elif self.token.value == "function":
                    definition = self.function_definition()
                    methods[definition.object.name] = definition.value
                else:
                    assignment = self.assignment()
                    statics[assignment.object.name] = assignment.value
            return Assignment(Variable(name), ClassCreate(name, methods, statics, parent_name))
        return self.function_definition()

    def function_definition(self):
        if self.token.value == "function":
            self.eat(TokenType.KEYWORD)
            name = self.eat(TokenType.NAME)
            self.eat(TokenType.GROUP, '(')
            var_arg_name = None
            if self.token.type == TokenType.ELLIPSIS:
                names = []
                var_arg_name = self.eat(TokenType.NAME)
            else:
                names = [self.eat(TokenType.NAME)]
                while self.token.type == TokenType.COMMA:
                    self.eat(TokenType.COMMA)
                    if self.token.type == TokenType.ELLIPSIS:
                        self.eat(TokenType.ELLIPSIS)
                        var_arg_name = self.eat(TokenType.NAME)
                        break
                    else:
                        names.append(self.eat(TokenType.NAME))
            self.eat(TokenType.GROUP, ')')
            body = self.statement_block()
            return Assignment(Variable(name), FunctionCreate(body, names, var_arg_name))
        return self.assignment_expr()

    def assignment(self):
        var = self.conditional_expr()
        if self.token.value == '=' and isinstance(var, IAssignable):
            self.eat(TokenType.OPERATOR)
            expr = self.assignment()
            return Assignment(var, expr)
        return var

    def conditional_expr(self):
        
