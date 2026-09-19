# Mission Authority Monotonicity

A powerful AI Agent requires a reliable mandate compiler.

Do not solve this by reducing the model to suggestions.

Instead separate:

SEMANTIC INTENT
from
AUTHORITY CEILING

The model may interpret semantics.
The server enforces authority ceilings.

Examples:

User:
"最多多花五十元"

Deterministic numeric evidence:
5000 minor units

Model:
50000 minor units

Resolved:
<= 5000

User:
"晚餐别动"

Local explicit polarity:
PROTECTED

Model:
MUTABLE

Resolved:
PROTECTED

User:
"后面那个室内馆别动"
No exact local alias match.

Model:
protected reference = "the later indoor museum"

Server:
resolve reference to an actual active-plan Activity.
If unique, protect it.
If unresolved, persist the unresolved reference and grant no mutation authority for that reference.

This is not conservative AI.
It is privilege-preserving intent compilation.
