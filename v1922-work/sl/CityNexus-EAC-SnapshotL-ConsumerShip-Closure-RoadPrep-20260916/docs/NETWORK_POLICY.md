# Public provider network policy

Snapshot K still hardcodes `trust_env=False` in public real-city discovery HTTP
clients.

That is unsafe as a permanent product policy.

The user's Windows machine has already shown a Mihomo network adapter and may
need a proxy path for public services such as Overpass/Nominatim.

Required:
- make provider proxy behaviour configurable;
- support direct and environment-proxy modes;
- do not print proxy credentials;
- record which network mode was used in provider diagnostics;
- on proxy-specific failure, provide a bounded alternate path when safe.

Do not permanently disable the user's environment proxy because one execution
environment had a bad proxy configuration.

Suggested policy:
- `AUTO`: use configured/default environment policy, then bounded alternate
  direct attempt for public provider failures where appropriate;
- `DIRECT`;
- `ENV_PROXY`.

The exact configuration name is an implementation choice.
