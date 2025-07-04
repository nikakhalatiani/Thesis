<start>    ::= <expr>
<expr>     ::= <list> ", " <expr> |  <list> ", " <list> ", " <list>
<list>     ::= "[" <elements>? "]"
<elements> ::= <number> | <number> ", " <elements>
<number>   ::= "-"?<integer> := str(produce_gaussian_integer())
<integer>  ::= <digit>+


def produce_gaussian_integer():
    import random
    mu = 0
    sigma = 100
    value = random.gauss(mu, sigma)
    return round(value)