import random

<start> ::= <first_set> ", " <second_set>
<set> ::= "{" <elements>? "}"
<first_set> ::= <set>
<second_set> ::= <set>
<elements> ::= <number> | <number> ", " <elements>
<number> ::=  "-"?<digit>+ := random.randint(-1000, 1000)
