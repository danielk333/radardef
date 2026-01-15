# Develop
---

During development you would most likely want the package editable and some more functionality:

```bash
    git clone --branch develop git@github.com:danielk333/radardef.git
    cd radardef
    pip install -e .[develop,type_checker,profiling,tests,documentation,mpi]
```
Trigger tests with:

```bash
    pytest
```
Run the type checker with:

```bash
    mypy src/radardef --follow-untyped-imports --disallow-untyped-defs -warn-unused-ignores
```

To run with MPI you are dependent on the *openmpi* library, with apt it can be installed as:

```bash
    apt install -y openmpi-bin libopenmpi-dev
```

Please refer to the style and contribution guidelines documented in the
[IRF Software Contribution Guide](https://danielk.developer.irf.se/software_contribution_guide/).
Generally external code-contributions are made trough a "Fork-and-pull"
workflow, while internal contributions follow the branching strategy outlined
in the contribution guide.

Please refer to [GitHub](https://github.com/danielk333/hardtarget/blob/main/DEVELOP.md/) for more
details.

