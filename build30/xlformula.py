# -*- coding: utf-8 -*-
"""xlformula.py — parser mínimo de fórmulas Excel (subconjunto usado por los textos vivos del libro) → AST JSON.

Gramática (precedencia de Excel, de menor a mayor):
  comparación (= <> < > <= >=)  <  concatenación (&)  <  aditiva (+ −)  <  multiplicativa (* /)  <  potencia (^)  <  unario (−)  <  átomo
Átomos: número · "cadena" ("" = comilla) · TRUE/FALSE · nombre definido · referencia 'Hoja'!$C$5 (o Hoja!C5) · FUNCION(args) · (expr)

AST (listas JSON, cabeza = tipo):
  ["num", 1.5] · ["str", "texto"] · ["bool", true] · ["name", "Tasa_Descuento"] · ["ref", "Motor_Sens", "B57"]
  ["call", "TEXT", [arg, …]] · ["bin", "&", a, b] · ["neg", a]
  Envolturas: ["f", AST, "=fórmula original"] para celdas-fórmula · ["tpl", [literal | AST, …]] para plantillas con llaves

Plantillas con llaves («… {TEXT(X_TIR,"0.0%")} …», Guía): parse_template(texto) → ["tpl", [ "literal" | AST, … ]]
"""
import re

TOKEN_RE = re.compile(r"""
    (?P<ws>\s+)
  | (?P<str>"(?:[^"]|"")*")
  | (?P<num>\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)
  | (?P<ref>'[^']+'!\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?|[A-Za-z_][A-Za-z0-9_]*!\$?[A-Z]{1,3}\$?\d+(?::\$?[A-Z]{1,3}\$?\d+)?)
  | (?P<name>[A-Za-z_][A-Za-z0-9_.]*)
  | (?P<op><>|<=|>=|[=<>&+\-*/^(),])
""", re.X)


class ParseError(Exception):
    pass


def tokenize(src):
    pos, out = 0, []
    while pos < len(src):
        m = TOKEN_RE.match(src, pos)
        if not m:
            raise ParseError(f"token inválido en {pos}: {src[pos:pos+20]!r} · {src!r}")
        pos = m.end()
        kind = m.lastgroup
        if kind == "ws":
            continue
        out.append((kind, m.group(kind)))
    return out


class Parser:
    def __init__(self, tokens):
        self.t = tokens
        self.i = 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def take(self, kind=None, val=None):
        k, v = self.peek()
        if kind and k != kind or val is not None and v != val:
            raise ParseError(f"esperaba {kind or ''}{val or ''}, hay {k}:{v!r}")
        self.i += 1
        return v

    # niveles
    def parse(self):
        node = self.comparison()
        if self.peek() != (None, None):
            raise ParseError(f"sobran tokens desde {self.peek()}")
        return node

    def comparison(self):
        node = self.concat()
        while self.peek()[0] == "op" and self.peek()[1] in ("=", "<>", "<", ">", "<=", ">="):
            op = self.take(); node = ["bin", op, node, self.concat()]
        return node

    def concat(self):
        node = self.additive()
        while self.peek() == ("op", "&"):
            self.take(); node = ["bin", "&", node, self.additive()]
        return node

    def additive(self):
        node = self.multiplicative()
        while self.peek()[0] == "op" and self.peek()[1] in ("+", "-"):
            op = self.take(); node = ["bin", op, node, self.multiplicative()]
        return node

    def multiplicative(self):
        node = self.power()
        while self.peek()[0] == "op" and self.peek()[1] in ("*", "/"):
            op = self.take(); node = ["bin", op, node, self.power()]
        return node

    def power(self):
        node = self.unary()
        while self.peek() == ("op", "^"):
            self.take(); node = ["bin", "^", node, self.unary()]
        return node

    def unary(self):
        if self.peek() == ("op", "-"):
            self.take(); return ["neg", self.unary()]
        if self.peek() == ("op", "+"):
            self.take(); return self.unary()
        return self.atom()

    def atom(self):
        k, v = self.peek()
        if k == "num":
            self.take(); return ["num", float(v) if ("." in v or "e" in v.lower()) else int(v)]
        if k == "str":
            self.take(); return ["str", v[1:-1].replace('""', '"')]
        if k == "ref":
            self.take()
            sheet, cell = v.rsplit("!", 1)
            return ["ref", sheet.strip("'"), cell.replace("$", "")]
        if k == "name":
            self.take()
            if v.upper() in ("TRUE", "FALSE"):
                return ["bool", v.upper() == "TRUE"]
            if self.peek() == ("op", "("):
                self.take()
                args = []
                if self.peek() != ("op", ")"):
                    args.append(self.comparison())
                    while self.peek() == ("op", ","):
                        self.take(); args.append(self.comparison())
                self.take("op", ")")
                return ["call", v.upper(), args]
            return ["name", v]
        if k == "op" and v == "(":
            self.take(); node = self.comparison(); self.take("op", ")"); return node
        raise ParseError(f"átomo inesperado {k}:{v!r}")


def parse_formula(src):
    """'=expr' o 'expr' → AST."""
    s = src[1:] if src.startswith("=") else src
    return Parser(tokenize(s)).parse()


BRACE_RE = re.compile(r"\{([^{}]+)\}")


def parse_template(text):
    """Texto con {expr} → ["tpl", [literal | AST, …]]. Sin llaves → devuelve el texto tal cual (str)."""
    if "{" not in text:
        return text
    parts, pos = [], 0
    for m in BRACE_RE.finditer(text):
        if m.start() > pos:
            parts.append(text[pos:m.start()])
        parts.append(parse_formula(m.group(1)))
        pos = m.end()
    if pos < len(text):
        parts.append(text[pos:])
    return ["tpl", parts]


def live(value):
    """Convierte un valor de las constantes del generador: '=…' → ["f", AST]; texto con {…} → ["tpl", …]; resto tal cual."""
    if isinstance(value, str):
        if value.startswith("="):
            return ["f", parse_formula(value), value]   # [2] = fórmula original (trazabilidad y pruebas contra el libro)
        return parse_template(value)
    return value


def names_in(node, acc=None):
    """Nombres definidos y referencias usados por un AST (para el resolutor)."""
    acc = set() if acc is None else acc
    if isinstance(node, list) and node:
        h = node[0]
        if h == "name":
            acc.add(node[1])
        elif h == "ref":
            acc.add(f"{node[1]}!{node[2]}")
        elif h == "call":
            for a in node[2]:
                names_in(a, acc)
        elif h in ("bin",):
            names_in(node[2], acc); names_in(node[3], acc)
        elif h == "neg":
            names_in(node[1], acc)
        elif h in ("f",):
            names_in(node[1], acc)
        elif h == "tpl":
            for p in node[1]:
                if isinstance(p, list):
                    names_in(p, acc)
    return acc


if __name__ == "__main__":
    import sys, json
    for s in sys.argv[1:]:
        print(json.dumps(live(s), ensure_ascii=False))
