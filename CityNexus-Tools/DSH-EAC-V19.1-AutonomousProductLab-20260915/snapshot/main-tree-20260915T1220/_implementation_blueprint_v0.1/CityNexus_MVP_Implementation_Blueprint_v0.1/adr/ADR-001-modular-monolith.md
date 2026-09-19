# ADR-001 - Modular monolith for coursework MVP

Decision: implement CityNexus as one backend service with internal bounded-context modules.

Reason: the project needs domain separation, not distributed-systems overhead. A modular monolith is easier to run, debug, test, submit and demonstrate while preserving seams for future extraction.

Rejected for MVP: microservices, event broker, service mesh.
