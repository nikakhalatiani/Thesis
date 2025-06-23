import random

<start>   ::= <expr>
<expr>    ::= <term1> ", " <term2> ", " <term3>
<term1>    ::= <number>
<term2>    ::= <number>
<term3>    ::= <number>
<number>  ::= "-"?<digit>+ := random.randint(-1000, 1000)