# SOUP Inventory (Template)

| SOUP ID | Component | Version | Source | Function | Safety Impact | Rationale | Controls | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SOUP-001 | Node.js | | | Runtime for Node bindings | Potential | | Pin version, CI build | CI logs |
| SOUP-002 | Python | | | Runtime for Python bindings | Potential | | Pin version, CI build | CI logs |
| SOUP-003 | pybind11 | | | C++/Python binding | Potential | | Pinned dependency | Build logs |
| SOUP-004 | googletest | | | C++ unit tests | None | | Test-only | Test logs |
| SOUP-005 | cmake-js | | | Node addon build tool | Potential | | Pinned dependency | Build logs |
