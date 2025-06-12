import random

<start> ::= <set> ", " <number>
<set> ::= "{" <elements>? "}"
<elements> ::= <number> | <number> ", " <elements>
<number> ::= "-"?<digit>+ := random.randint(-1000, 1000)
