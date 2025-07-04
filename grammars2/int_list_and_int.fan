<start> ::= <list> ", " <extra_number>
<list> ::= "[" <elements>? "]"
<elements> ::= <number> | <number> ", " <elements>
<number> ::= <signed_integer>
<extra_number> ::= <signed_integer>
<signed_integer> ::= "-"?<integer> := str(produce_gaussian_integer())
<integer> ::= <digit>+

def produce_gaussian_integer():
    import random
    mu = 0
    sigma = 100
    value = random.gauss(mu, sigma)
    return round(value)