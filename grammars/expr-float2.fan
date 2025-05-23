import random

<start>   ::= <expr>
<expr>    ::= <term> " + " <expr> | <term> " - " <expr> | <term>
<term>    ::= <term> " * " <factor> | <term> " / " <factor> | <factor>
<factor>  ::= "+" <factor> | "-" <factor> | "(" <expr> ")" | <int> | <float>
<int>     ::= <digit> | <lead_digit> <digits>
<float>   ::= <int> "." <digits>
<digits>  ::= <digit>+ := random.randint(0, 10000)
<lead_digit> ::= <digit> := random.randint(1, 9)