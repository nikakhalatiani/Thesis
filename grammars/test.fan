import random

<start>   ::= <expr>
<expr>    ::= <term> | <term> ", " <expr>

<term>    ::= <number>
<number>  ::= "-"?<digit>+ := random.randint(-1000, 1000)
