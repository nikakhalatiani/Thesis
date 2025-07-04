<start>    ::= <expr>
<expr>     ::= <set> ", " <expr> | <set> ", " <set> ", " <set>
<set>      ::= "{" <elements>? "}"
<elements> ::= <number> | <number> ", " <elements>
<number>   ::= "-"?<float> := str(produce_gaussian_float())
<float>    ::= <digit>+ "." <digit>+

def produce_gaussian_float():
    import random
    mu = 0
    sigma = 100
    value = random.gauss(mu, sigma)
    return value