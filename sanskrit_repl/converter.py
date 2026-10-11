"""Convert English spellings of Sanskrit REPL code into Devanagari spellings."""

from __future__ import annotations

import ast
import io
import tokenize

from .interpreter import normalize


class ConversionError(ValueError):
    """The input cannot be converted as runnable Sanskrit REPL code."""


WORDS = {
    "if": "यदि", "elif": "अन्ययदि", "else": "अन्यथा",
    "while": "यावत्", "for": "प्रत्येक", "in": "मध्ये",
    "def": "कार्य", "func": "कार्य", "return": "प्रत्यावर्तय",
    "break": "विराम", "continue": "अग्रे",
    "and": "च", "or": "वा", "not": "न",
    "True": "सत्यम्", "False": "असत्यम्", "None": "शून्यम्",
    "true": "सत्यम्", "false": "असत्यम्", "nil": "शून्यम्",
    "let": "स्थापय",
}

BUILTINS = {
    "print": "मुद्रय", "len": "लम्बाई", "range": "परास",
    "sum": "योग", "min": "न्यूनतम", "max": "अधिकतम",
    "sorted": "क्रम", "reversed": "उलट", "list": "सूची",
    "dict": "कोश", "set": "समुच्चय", "enumerate": "गणना",
    "zip": "युग्म", "int": "पूर्णांक", "float": "दशमलव",
    "str": "अक्षर", "bool": "बूल", "abs": "निरपेक्ष",
    "all": "सर्व", "any": "कोई", "make": "बनाओ",
    "append": "जोड़ो", "cap": "क्षमता", "copy": "प्रतिलिपि",
    "sqrt": "वर्गमूल",
}

COMMANDS = {"calculate": "गणय", "show": "दर्शय"}
SPOKEN_OPERATORS = {"plus": "जोड़", "minus": "घटा", "times": "गुणा"}


def _unsupported(node: ast.AST) -> None:
    raise ConversionError(f"Unsupported {type(node).__name__} at line {getattr(node, 'lineno', 1)}")


def _validate_expression(node: ast.AST) -> None:
    if isinstance(node, (ast.Constant, ast.Name)):
        return
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        for value in node.elts:
            _validate_expression(value)
    elif isinstance(node, ast.Dict):
        for key, value in zip(node.keys, node.values):
            if key is None:
                _unsupported(node)
            _validate_expression(key)
            _validate_expression(value)
    elif isinstance(node, ast.Slice):
        for value in (node.lower, node.upper, node.step):
            if value is not None:
                _validate_expression(value)
    elif isinstance(node, ast.Subscript):
        _validate_expression(node.value)
        _validate_expression(node.slice)
    elif isinstance(node, ast.BinOp):
        if not isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)):
            _unsupported(node)
        _validate_expression(node.left)
        _validate_expression(node.right)
    elif isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, (ast.UAdd, ast.USub, ast.Not)):
            _unsupported(node)
        _validate_expression(node.operand)
    elif isinstance(node, ast.BoolOp):
        if not isinstance(node.op, (ast.And, ast.Or)):
            _unsupported(node)
        for value in node.values:
            _validate_expression(value)
    elif isinstance(node, ast.Compare):
        supported = (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.In, ast.Is, ast.IsNot)
        if any(not isinstance(op, supported) for op in node.ops):
            _unsupported(node)
        _validate_expression(node.left)
        for value in node.comparators:
            _validate_expression(value)
    elif isinstance(node, ast.IfExp):
        for value in (node.test, node.body, node.orelse):
            _validate_expression(value)
    elif isinstance(node, ast.Call):
        _validate_expression(node.func)
        for value in node.args:
            _validate_expression(value)
        for keyword in node.keywords:
            if keyword.arg is None:
                _unsupported(node)
            _validate_expression(keyword.value)
    elif isinstance(node, ast.JoinedStr):
        for value in node.values:
            _validate_expression(value)
    elif isinstance(node, ast.FormattedValue):
        if node.format_spec is not None:
            _unsupported(node)
        _validate_expression(node.value)
    else:
        _unsupported(node)


def _validate_target(node: ast.AST) -> None:
    if isinstance(node, ast.Name):
        return
    if isinstance(node, (ast.List, ast.Tuple)):
        for value in node.elts:
            _validate_target(value)
    elif isinstance(node, ast.Subscript):
        _validate_expression(node.value)
        _validate_expression(node.slice)
    else:
        _unsupported(node)


def _validate_statements(statements: list[ast.stmt], *, in_function: bool = False, in_loop: bool = False) -> None:
    for node in statements:
        if isinstance(node, ast.Expr):
            _validate_expression(node.value)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                _validate_target(target)
            _validate_expression(node.value)
        elif isinstance(node, ast.AugAssign):
            if not isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod)):
                _unsupported(node)
            _validate_target(node.target)
            _validate_expression(node.value)
        elif isinstance(node, ast.If):
            _validate_expression(node.test)
            _validate_statements(node.body, in_function=in_function, in_loop=in_loop)
            _validate_statements(node.orelse, in_function=in_function, in_loop=in_loop)
        elif isinstance(node, (ast.While, ast.For)):
            if isinstance(node, ast.While):
                _validate_expression(node.test)
            else:
                _validate_target(node.target)
                _validate_expression(node.iter)
            _validate_statements(node.body, in_function=in_function, in_loop=True)
            _validate_statements(node.orelse, in_function=in_function, in_loop=in_loop)
        elif isinstance(node, ast.FunctionDef):
            arguments = node.args
            if (node.decorator_list or arguments.vararg or arguments.kwarg or arguments.kwonlyargs
                    or node.returns is not None or any(arg.annotation for arg in arguments.posonlyargs + arguments.args)):
                _unsupported(node)
            for value in arguments.defaults:
                _validate_expression(value)
            _validate_statements(node.body, in_function=True)
        elif isinstance(node, ast.Return):
            if not in_function:
                _unsupported(node)
            if node.value is not None:
                _validate_expression(node.value)
        elif isinstance(node, (ast.Break, ast.Continue)):
            if not in_loop:
                _unsupported(node)
        elif isinstance(node, ast.Pass):
            pass
        else:
            _unsupported(node)


def _bound_names(tree: ast.AST) -> set[str]:
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            names.add(node.name)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
    return names


def convert_to_sanskrit(source: str) -> str:
    """Convert supported English code, preserving all non-word source text."""
    try:
        tree = ast.parse(normalize(source), mode="exec")
    except SyntaxError as error:
        raise ConversionError(f"Syntax at line {error.lineno}: {error.msg}") from error
    _validate_statements(tree.body)
    shadowed = _bound_names(tree)

    lines = source.splitlines(keepends=True)
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line))
    edits = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
        spoken_lines = set()
        for token in tokens:
            if token.type == tokenize.NAME and token.string in COMMANDS:
                line = lines[token.start[0] - 1]
                following = line[token.end[1]:]
                if not line[:token.start[1]].strip() and following and following[0].isspace() and following.strip():
                    spoken_lines.add(token.start[0])
        skip = set()
        for index, token in enumerate(tokens):
            if index in skip:
                continue
            if token.type != tokenize.NAME:
                continue
            word = token.string
            replacement = WORDS.get(word)
            is_keyword_argument = (index + 1 < len(tokens) and tokens[index + 1].string == "=")
            if (replacement is None and word not in shadowed
                    and BUILTINS.get(word) not in shadowed and not is_keyword_argument):
                replacement = BUILTINS.get(word)
            if token.start[0] in spoken_lines:
                if word in COMMANDS:
                    replacement = COMMANDS[word]
                elif word in SPOKEN_OPERATORS:
                    replacement = SPOKEN_OPERATORS[word]
                elif word == "divided" and index + 1 < len(tokens):
                    next_token = tokens[index + 1]
                    if (next_token.type == tokenize.NAME and next_token.string == "by"
                            and next_token.start[0] == token.start[0]):
                        start = starts[token.start[0] - 1] + token.start[1]
                        end = starts[next_token.end[0] - 1] + next_token.end[1]
                        edits.append((start, end, "भाग"))
                        skip.add(index + 1)
                        continue
            if replacement is not None and replacement != word:
                start = starts[token.start[0] - 1] + token.start[1]
                end = starts[token.end[0] - 1] + token.end[1]
                edits.append((start, end, replacement))
    except tokenize.TokenError as error:
        raise ConversionError(f"Tokenization failed: {error.args[0]}") from error

    result = source
    for start, end, replacement in reversed(edits):
        result = result[:start] + replacement + result[end:]
    return result
