"""Parser and tree-walking runtime for the Sanskrit-inspired language."""

from __future__ import annotations

import ast
import math
import operator
import re
import unicodedata
from dataclasses import dataclass


class SanskritError(Exception):
    pass


KEYWORDS = {
    "यदि": "if", "अन्ययदि": "elif", "अन्यथा": "else",
    "यावत्": "while", "प्रत्येक": "for", "मध्ये": "in",
    "कार्य": "def", "प्रत्यावर्तय": "return", "विराम": "break",
    "अग्रे": "continue", "च": "and", "वा": "or", "न": "not",
    "सत्यम्": "True", "असत्यम्": "False", "शून्यम्": "None",
    "func": "def", "true": "True", "false": "False", "nil": "None",
}

NUMBER_WORDS = {
    "शून्य": "0", "एक": "1", "दो": "2", "तीन": "3", "चार": "4",
    "पाँच": "5", "पांच": "5", "छह": "6", "सात": "7", "आठ": "8",
    "नौ": "9", "दस": "10",
}


def _intent_lines(source: str) -> str:
    """Handle a few explicit spoken-style commands without guessing at code."""
    converted = []
    for line in source.splitlines(keepends=True):
        match = re.match(r"^(\s*)(गणय|दर्शय|calculate|show)\s+(.+?)(\r?\n)?$", line, re.I)
        if not match:
            converted.append(line)
            continue
        indent, command, expression, newline = match.groups()
        expression = expression.strip().rstrip("।?")
        expression = expression.translate(str.maketrans("०१२३४५६७८९", "0123456789"))
        for word, digit in NUMBER_WORDS.items():
            expression = re.sub(rf"(?<!\w){word}(?!\w)", digit, expression)
        expression = re.sub(r"(?<!\S)(?:जोड़|plus)(?!\S)", "+", expression, flags=re.I)
        expression = re.sub(r"(?<!\S)(?:घटा|minus)(?!\S)", "-", expression, flags=re.I)
        expression = re.sub(r"(?<!\S)(?:गुणा|times)(?!\S)", "*", expression, flags=re.I)
        expression = re.sub(r"(?<!\S)(?:भाग|divided by)(?!\S)", "/", expression, flags=re.I)
        converted.append(f"{indent}मुद्रय({expression}){newline or ''}")
    return "".join(converted)


def normalize(source: str) -> str:
    """Translate language words while leaving quoted strings untouched."""
    source = _intent_lines(source)
    words = sorted((*KEYWORDS, "स्थापय", "let"), key=len, reverse=True)

    def identifier_char(char):
        return char == "_" or bool(char and unicodedata.category(char)[0] in "LMN")

    result = []
    i = 0
    while i < len(source):
        char = source[i]
        if char == "#":
            end = source.find("\n", i)
            if end < 0:
                end = len(source)
            result.append(source[i:end])
            i = end
            continue
        if char in "\"'":
            quote = char * (3 if source.startswith(char * 3, i) else 1)
            end = i + len(quote)
            while end < len(source):
                if source[end] == "\\":
                    end += 2
                elif source.startswith(quote, end):
                    end += len(quote)
                    break
                else:
                    end += 1
            result.append(source[i:end])
            i = end
            continue
        if source.startswith(":=", i):
            result.append("=")
            i += 2
            continue
        word = next((word for word in words
                     if source.startswith(word, i)
                     and (i == 0 or not identifier_char(source[i - 1]))
                     and (i + len(word) == len(source) or not identifier_char(source[i + len(word)]))), None)
        if word is not None:
            result.append("" if word in ("स्थापय", "let") else KEYWORDS[word])
            i += len(word)
            continue
        result.append(char)
        i += 1
    return "".join(result)


class _Return(Exception):
    def __init__(self, value):
        self.value = value


class _Break(Exception):
    pass


class _Continue(Exception):
    pass


@dataclass
class _Function:
    name: str
    params: list[str]
    body: list[ast.stmt]
    closure: list[dict]
    defaults: list[object]


class Interpreter:
    """Persistent interpreter. Each execute call has a fresh step allowance."""

    def __init__(self, max_steps: int = 100_000):
        self.max_steps = max_steps
        self.steps = 0
        self.frames: list[dict] = [{}]
        self.output: list[str] = []
        self._builtins = self._make_builtins()

    def _make_builtins(self):
        def display(*values, sep=" ", end="\n"):
            if not isinstance(sep, str) or not isinstance(end, str):
                raise SanskritError("sep and end must be text")
            self.output.append(sep.join(str(x) for x in values) + end)

        def make(kind, size=0):
            if kind in ("सूची", "list"):
                return [None] * size
            if kind in ("कोश", "dict"):
                return {}
            raise SanskritError("बनाओ expects सूची/list or कोश/dict")

        def append(seq, *values):
            if not isinstance(seq, list):
                raise SanskritError("जोड़ो expects a list")
            return seq + list(values)

        def capacity(seq):
            return len(seq)

        def copy_into(dst, src):
            if not isinstance(dst, list) or not isinstance(src, (list, tuple)):
                raise SanskritError("प्रतिलिपि expects two lists")
            n = min(len(dst), len(src))
            dst[:n] = src[:n]
            return n

        funcs = {
            "मुद्रय": display, "print": display,
            "लम्बाई": len, "len": len, "परास": range, "range": range,
            "योग": sum, "sum": sum, "न्यूनतम": min, "min": min,
            "अधिकतम": max, "max": max, "क्रम": sorted, "sorted": sorted,
            "उलट": lambda x: list(reversed(x)), "reversed": lambda x: list(reversed(x)),
            "सूची": list, "list": list, "कोश": dict, "dict": dict,
            "समुच्चय": set, "set": set, "गणना": enumerate, "enumerate": enumerate,
            "युग्म": zip, "zip": zip, "पूर्णांक": int, "int": int,
            "दशमलव": float, "float": float, "अक्षर": str, "str": str,
            "बूल": bool, "bool": bool, "निरपेक्ष": abs, "abs": abs,
            "सर्व": all, "all": all, "कोई": any, "any": any,
            "बनाओ": make, "make": make, "जोड़ो": append, "append": append,
            "क्षमता": capacity, "cap": capacity,
            "प्रतिलिपि": copy_into, "copy": copy_into,
            "वर्गमूल": math.sqrt, "sqrt": math.sqrt,
        }
        return funcs

    def _tick(self, node):
        self.steps += 1
        if self.steps > self.max_steps:
            raise SanskritError("Execution limit reached; check for an endless loop")

    def _lookup(self, name):
        for frame in reversed(self.frames):
            if name in frame:
                return frame[name]
        if name in self._builtins:
            return self._builtins[name]
        raise SanskritError(f"Unknown name: {name}")

    def _assign(self, target, value):
        if isinstance(target, ast.Name):
            self.frames[-1][target.id] = value
        elif isinstance(target, (ast.Tuple, ast.List)):
            try:
                values = list(value)
            except TypeError as exc:
                raise SanskritError("Cannot unpack this value") from exc
            if len(values) != len(target.elts):
                raise SanskritError("Unpacking needs the same number of values")
            for item, val in zip(target.elts, values):
                self._assign(item, val)
        elif isinstance(target, ast.Subscript):
            obj = self._eval(target.value)
            obj[self._eval(target.slice)] = value
        else:
            raise SanskritError("Invalid assignment target")

    def _eval(self, node):
        self._tick(node)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return self._lookup(node.id)
        if isinstance(node, ast.List):
            return [self._eval(x) for x in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(self._eval(x) for x in node.elts)
        if isinstance(node, ast.Set):
            return {self._eval(x) for x in node.elts}
        if isinstance(node, ast.Dict):
            return {self._eval(k): self._eval(v) for k, v in zip(node.keys, node.values)}
        if isinstance(node, ast.Slice):
            return slice(*(self._eval(x) if x is not None else None for x in (node.lower, node.upper, node.step)))
        if isinstance(node, ast.Subscript):
            return self._eval(node.value)[self._eval(node.slice)]
        if isinstance(node, ast.BinOp):
            ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                   ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
                   ast.Mod: operator.mod, ast.Pow: operator.pow}
            fn = ops.get(type(node.op))
            if fn is None:
                raise SanskritError("Unsupported arithmetic operator")
            return fn(self._eval(node.left), self._eval(node.right))
        if isinstance(node, ast.UnaryOp):
            ops = {ast.USub: operator.neg, ast.UAdd: operator.pos, ast.Not: operator.not_}
            fn = ops.get(type(node.op))
            if fn is None:
                raise SanskritError("Unsupported unary operator")
            return fn(self._eval(node.operand))
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                value = True
                for item in node.values:
                    value = self._eval(item)
                    if not value:
                        return value
                return value
            if isinstance(node.op, ast.Or):
                value = False
                for item in node.values:
                    value = self._eval(item)
                    if value:
                        return value
                return value
        if isinstance(node, ast.Compare):
            ops = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt,
                   ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge,
                   ast.In: lambda a, b: a in b, ast.NotIn: lambda a, b: a not in b,
                   ast.Is: operator.is_, ast.IsNot: operator.is_not}
            left = self._eval(node.left)
            for op, right_node in zip(node.ops, node.comparators):
                right = self._eval(right_node)
                fn = ops.get(type(op))
                if fn is None:
                    raise SanskritError("Unsupported comparison")
                if not fn(left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.IfExp):
            return self._eval(node.body if self._eval(node.test) else node.orelse)
        if isinstance(node, ast.Call):
            fn = self._eval(node.func)
            args = [self._eval(arg) for arg in node.args]
            kwargs = {kw.arg: self._eval(kw.value) for kw in node.keywords if kw.arg is not None}
            if len(kwargs) != len(node.keywords):
                raise SanskritError("Expanded keyword arguments are unsupported")
            if isinstance(fn, _Function):
                return self._call_user(fn, args, kwargs)
            if fn not in self._builtins.values():
                raise SanskritError("Only language functions can be called")
            return fn(*args, **kwargs)
        if isinstance(node, ast.JoinedStr):
            return "".join(str(self._eval(x)) for x in node.values)
        if isinstance(node, ast.FormattedValue):
            if node.format_spec is not None:
                raise SanskritError("Format specifications are unsupported")
            return self._eval(node.value)
        raise SanskritError(f"Unsupported expression: {type(node).__name__}")

    def _call_user(self, fn, args, kwargs):
        if len(args) > len(fn.params):
            raise SanskritError(f"{fn.name} takes at most {len(fn.params)} arguments")
        required = len(fn.params) - len(fn.defaults)
        local = dict(zip(fn.params, args))
        for name, value in kwargs.items():
            if name not in fn.params or name in local:
                raise SanskritError(f"Unexpected or repeated argument: {name}")
            local[name] = value
        for name, value in zip(fn.params[required:], fn.defaults):
            local.setdefault(name, value)
        if len(local) != len(fn.params):
            raise SanskritError(f"Missing argument for {fn.name}")
        previous = self.frames
        self.frames = fn.closure + [local]
        try:
            try:
                self._block(fn.body)
            except _Return as result:
                return result.value
            return None
        finally:
            self.frames = previous

    def _block(self, body):
        for node in body:
            self._stmt(node)

    def _stmt(self, node):
        self._tick(node)
        if isinstance(node, ast.Expr):
            return self._eval(node.value)
        if isinstance(node, ast.Assign):
            value = self._eval(node.value)
            for target in node.targets:
                self._assign(target, value)
            return
        if isinstance(node, ast.AugAssign):
            ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                   ast.Div: operator.truediv, ast.Mod: operator.mod}
            fn = ops.get(type(node.op))
            if fn is None:
                raise SanskritError("Unsupported assignment operator")
            self._assign(node.target, fn(self._eval(node.target), self._eval(node.value)))
            return
        if isinstance(node, ast.If):
            self._block(node.body if self._eval(node.test) else node.orelse)
            return
        if isinstance(node, ast.While):
            while self._eval(node.test):
                try:
                    self._block(node.body)
                except _Continue:
                    continue
                except _Break:
                    break
            else:
                self._block(node.orelse)
            return
        if isinstance(node, ast.For):
            for value in self._eval(node.iter):
                self._tick(node)
                self._assign(node.target, value)
                try:
                    self._block(node.body)
                except _Continue:
                    continue
                except _Break:
                    break
            else:
                self._block(node.orelse)
            return
        if isinstance(node, ast.FunctionDef):
            if node.decorator_list or node.args.vararg or node.args.kwarg or node.args.kwonlyargs:
                raise SanskritError("Decorators and variable arguments are unsupported")
            params = [arg.arg for arg in node.args.posonlyargs + node.args.args]
            defaults = [self._eval(x) for x in node.args.defaults]
            self.frames[-1][node.name] = _Function(node.name, params, node.body, list(self.frames), defaults)
            return
        if isinstance(node, ast.Return):
            if len(self.frames) == 1:
                raise SanskritError("प्रत्यावर्तय is only valid inside a function")
            raise _Return(self._eval(node.value) if node.value else None)
        if isinstance(node, ast.Break):
            raise _Break()
        if isinstance(node, ast.Continue):
            raise _Continue()
        if isinstance(node, ast.Pass):
            return
        raise SanskritError(f"Unsupported statement: {type(node).__name__}")

    def execute(self, source: str) -> str:
        self.output = []
        self.steps = 0
        try:
            tree = ast.parse(normalize(source), mode="exec")
            result = None
            for node in tree.body:
                result = self._stmt(node)
            if result is not None:
                self.output.append(repr(result) + "\n")
            return "".join(self.output)
        except SanskritError:
            raise
        except SyntaxError as exc:
            raise SanskritError(f"Syntax at line {exc.lineno}: {exc.msg}") from exc
        except (_Break, _Continue) as exc:
            raise SanskritError("विराम/अग्रे is only valid inside a loop") from exc
        except (TypeError, ValueError, IndexError, KeyError, ZeroDivisionError, OverflowError, RecursionError) as exc:
            raise SanskritError(f"{type(exc).__name__}: {exc}") from exc
