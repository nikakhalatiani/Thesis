<start>   ::= <expr>
<expr>    ::= <term> ", " <expr> | <term> ", " <term> ", " <term>
<term>    ::= <number>
<number>  ::= "-"?<integer> := str(produce_gaussian_integer())
<integer> ::= <digit>+


def produce_gaussian_integer():
    import random
    mu = 0
    sigma = 400
    value = random.gauss(mu, sigma)
    return round(value)
