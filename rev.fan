<start> ::= <pair>

<pair> ::= <term1> " + " <term2> " = " <term2> " + " <term1>

<term1> ::= <number>
<term2> ::= <number>

<number> ::= <nonzero_digit> <digit>* | <digit>

<digit> ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
<nonzero_digit> ::= "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"

