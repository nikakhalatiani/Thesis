<start> ::= <list> ", " <extra_number>
<list> ::= "[" <elements>? "]"
<elements> ::= <number> | <number> ", " <elements>
<number> ::= <signed_float>
<extra_number> ::= <signed_float>
<signed_float> ::= "-"?<float> := str(produce_gaussian_float())
<float> ::= <digit>+ "." <digit>+


def produce_gaussian_float():
    import random
    mu = 0
    sigma = 100
    value = random.gauss(mu, sigma)
    return value