import random

<start>   ::= <expr>
<expr>    ::= <term> ", " <expr> | <term>
<term>    ::= <number>
<number>  ::= "-"?<digit>+ := random.randint(-1000, 1000)
