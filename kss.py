from typing import Dict, List
from kristybot import Kristy


class Statement:
    def execute(self, kristy: Kristy, chat: int, variables: Dict[str, object]):
        pass


class KristyScheduleScript:
    def __init__(self, string: str, body: List[Statement]):
        self.string = string
        self.body: List[Statement] = body
        self.variables: Dict[str, object] = {}

    def execute(self, kristy: Kristy, chat: int, variables: Dict[str, object]):
        for stmt in self.body:
            stmt.execute(kristy, chat, variables)

    def __str__(self):
        return self.string

    def __repr__(self):
        return str(self)


class BuiltinFnCallStmt(Statement):
    def __init__(self, string: str):
        if string.startswith('ОТПРАВИТЬ ТЕКСТ '):
            self.inner = BuiltinFnCallStmt.SendTextFn(string[len('ОТПРАВИТЬ ТЕКСТ '):])
        elif string.startswith('ОТПРАВИТЬ ВЛОЖЕНИЕ '):
            self.inner = BuiltinFnCallStmt.SendAttachmentFn(string[len('ОТПРАВИТЬ ВЛОЖЕНИЕ '):])
        elif string.startswith('ВЫПОЛНИТЬ СЦЕНАРИЙ '):
            self.inner = BuiltinFnCallStmt.ExecNamedScriptFn(string[len('ВЫПОЛНИТЬ СЦЕНАРИЙ '):])
        else:
            raise SyntaxError()

    def execute(self, kristy: Kristy, chat: int, variables: Dict[str, object]):
        self.inner.execute(kristy, chat, variables)

    class SendTextFn(Statement):
        def __init__(self, string: str):
            self.msg = string

        def execute(self, kristy: Kristy, chat: int, variables: Dict[str, object]):
            msg = _expand_variables(self.msg, variables)
            kristy.send(2E9+chat, msg)

    class SendAttachmentFn(Statement):
        def __init__(self, string: str):
            self.attachment_tag = string

        def execute(self, kristy: Kristy, chat: int, variables: Dict[str, object]):
            attachment_tag = _expand_variables(self.attachment_tag, variables)
            attachment = kristy.db.get_attachment(chat, attachment_tag)
            kristy.send(2E9+chat, attachment["message"], attachment["attachments"])

    class ExecNamedScriptFn(Statement):
        def __init__(self, string: str):
            self.script_name = string

        def execute(self, kristy: Kristy, chat: int, variables: Dict[str, object]):
            script_name = _expand_variables(self.script_name, variables)
            kristy.tt_data.named_scripts[chat][script_name].execute(kristy, chat, variables)


class IfStmt(Statement):
    def __init__(self, string: str):
        parts = string.split(' ТО ', 1)
        condition = parts[0]
        self.body = BuiltinFnCallStmt(parts[1].strip())

        if condition.count('>=') == 1:
            self.op = '>='
            cmp_sides = condition.split('>=')
        elif condition.count('<=') == 1:
            self.op = '<='
            cmp_sides = condition.split('<=')
        elif condition.count('>') == 1:
            self.op = '>'
            cmp_sides = condition.split('>')
        elif condition.count('<') == 1:
            self.op = '<'
            cmp_sides = condition.split('<')
        elif condition.count('=') == 1:
            self.op = '='
            cmp_sides = condition.split('=')
        else:
            raise RuntimeError()

        self.lhs = cmp_sides[0]
        self.rhs = cmp_sides[1]

    def execute(self, kristy: Kristy, chat: int, variables: Dict[str, object]):
        if self._evaluate(kristy, chat, variables):
            self.body.execute(kristy, chat, variables)

    def _evaluate(self, kristy: Kristy, chat: int, variables: Dict[str, object]):
        lhs = int(_expand_variables(self.lhs, variables))
        rhs = int(_expand_variables(self.rhs, variables))

        if self.op == '>=':
            return lhs >= rhs
        elif self.op == '<=':
            return lhs <= rhs
        elif self.op == '>':
            return lhs > rhs
        elif self.op == '<':
            return lhs < rhs
        elif self.op == '=':
            return lhs == rhs
        else:
            raise SyntaxError()


def _expand_variables(string: str, variables: Dict[str, object]) -> str:
    for var_name, var_value in variables.items():
        string = string.replace('{' + var_name + '}', str(var_value))

    return string


def parse(string: str) -> KristyScheduleScript:
    body: List[Statement] = []
    string = string.strip()

    for stmt in string.split(';'):
        stmt = stmt.strip()

        if len(stmt) == 0:
            continue

        if stmt.startswith('ЕСЛИ '):
            body.append(IfStmt(stmt[len('ЕСЛИ '):]))
        else:
            body.append(BuiltinFnCallStmt(stmt))

    return KristyScheduleScript(string, body)
