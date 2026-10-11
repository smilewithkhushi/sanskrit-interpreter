# Sanskrit REPL language rules

The language is a deliberately small, Python-like subset. Devanagari and English
spellings of control words and built-ins are accepted. Indentation defines blocks.
The interpreter parses normalized source with Python's parser, validates the
supported subset, then evaluates that tree itself. It does not execute Python source.

## Names and assignment

- Identifiers follow Python's Unicode identifier rules. Sanskrit names can be used
  for variables and function names.
- `x := value` and `x = value` both assign a name. `:=` does **not** have Go's
  declaration or scoping rules. `स्थापय` and `let` before an assignment are optional.
- An assignment writes into the current function's local frame, or the persistent
  top-level frame. A function can read names from its enclosing frames. Assigning
  the same name inside a function creates a local name; there is no `global` or
  `nonlocal` declaration.
- List or tuple unpacking requires exactly the same number of values. Subscript
  assignment, such as `items[0] = 4`, mutates the selected collection.
- Top-level variables and functions persist across terminal or browser REPL runs.
  `:reset` in the terminal or **Reset state** in the browser clears that state.
  Browser state belongs to one browser session.

## Functions and control flow

- `कार्य` / `func` / `def` defines a function. Positional parameters, keyword calls,
  and trailing default values are supported. Defaults are evaluated when the
  function is defined. `प्रत्यावर्तय` / `return` returns a value; reaching the end
  returns `शून्यम्` / `None`.
- `यदि` / `if`, `अन्ययदि` / `elif`, `अन्यथा` / `else`, `यावत्` / `while`,
  and `प्रत्येक` / `for` use Python-like conditions and indentation. `विराम` /
  `break` and `अग्रे` / `continue` work inside loops. `while` and `for` may have an
  `else` block that runs if the loop finishes without `break`.
- Values use Python-like truthiness. `च` / `and` and `वा` / `or` short-circuit and
  return one of their operands. `न` / `not` returns a boolean.
- Calls consume a fixed execution-step allowance, initially 100,000 steps per
  `execute` call. Errors stop the current run; assignments already made remain.

## Values and expressions

Numbers, strings, booleans, `शून्यम्` / `None`, lists, tuples, dictionaries, and sets
are supported, along with arithmetic, comparisons, indexing, slices, and basic
f-strings. List and dictionary comprehensions, imports, attributes, classes,
decorators, generators, and file I/O are outside the supported subset. The
interpreter and VS Code language server report unsupported syntax before running.

## Built-in behavior

Most built-ins have the same arguments and return values as their named Python
counterparts (`योग` / `sum`, `लम्बाई` / `len`, `परास` / `range`, etc.), subject to
the interpreter's supported value types. These built-ins have language-specific
behavior:

| Built-in | Behavior |
| --- | --- |
| `मुद्रय` / `print` | Adds text to this run's output; returns `None`. Supports `sep` and `end` strings. |
| `बनाओ` / `make` | `make("सूची", n)` returns a list of `n` `None` values; `make("कोश")` returns an empty dictionary. |
| `जोड़ो` / `append` | Returns a **new** list with the supplied values appended; does not mutate the input list. |
| `क्षमता` / `cap` | Returns the collection's current length. There is no separate reserved capacity. |
| `प्रतिलिपि` / `copy` | Copies items into an existing destination list, mutates it, and returns the number copied. |

At the terminal or browser REPL, a final expression with a non-`None` result is
displayed using its representation. `मुद्रय` is the explicit way to print text.

## Errors

Syntax errors, unsupported constructs, unknown names, type errors, and execution
limits stop the current run. Error messages include a one-based source line and,
where available, a one-based column. Source locations point to the original
Sanskrit or English input, including when keyword normalization changes its length.
