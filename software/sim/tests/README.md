# Simulator and protocol tests

Host tests copied from `wa1hco/k3ng_rotator_controller` at
`27156ad04ab3bf05b93761b5a9612c2a382143ac`. See `../README.md`.

```bash
make test
```

That builds the physics, protocol-shim, and feature-config cases and
runs them. It does not start a firmware process.

```bash
K3NG_BINARY=/path/to/gs232-binary make integration
```

The integration binary forks a program that speaks Yaesu GS-232 on
stdin/stdout and answers `C2` with `AZ=nnn`. Upstream, that program is
the K3NG native build. It is not part of this repository. See the
retargeting notes in `../README.md`.
