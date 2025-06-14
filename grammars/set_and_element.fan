import random

<start> ::= <set> ", " <number_to_add>
<set> ::= "{" <elements>? "}"
<elements> ::= <number> | <number> ", " <elements>
<number> ::= "-"?<digit>+ := random.randint(-1000, 1000)
<number_to_add> ::= "-"?<digit>+ := random.randint(-1000, 1000)
