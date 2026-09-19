# Public-provider network policy V2

Snapshot L correctly removed the permanent `trust_env=False`.

But the source comments currently promise more than the implementation.

## Acceptable choices

### Option A — simple truthful AUTO

`AUTO`:
- honour environment proxy configuration;
- no automatic direct retry.

Then update comments/docs accordingly.

### Option B — bounded fallback AUTO

`AUTO`:
1. try environment proxy;
2. only on qualifying connection/proxy failure, retry once directly;
3. preserve normal provider timeout limits;
4. do not retry on ordinary HTTP application errors;
5. never log proxy secrets.

Either choice is acceptable.

The implementation and documentation must agree.

## Modes

Keep explicit:
- AUTO
- ENV_PROXY
- DIRECT

This is important for the user's Windows + Mihomo environment.
