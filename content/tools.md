| Tool/Compiler | C++20 Modules | Version Support |
|---------------|---------------|----------------|
| MSVC 2022     |  ✅      |  17.6         |
| Clang         |   Partial      |         17       |
| Apple Clang   |  ❌            |  ❌            |
| GCC           |  ❌            |         ❌       |

| Tool/Compiler | C++23 `import std` | Version Support |
|---------------|---------------------|-----------------|
| MSVC 2022     |  Partial            |  17.10          |
| Clang         |  ❌            |  ❌              |
| Apple Clang   |  ❌                 |  ❌              |
| GCC           |  ❌                 |     ❌            |

| Tool     | C++20 Modules | C++23 `import std` | Issue |
|----------|----------------|--------------------|-------|
| CMake    | ✅ 3.28             | ✅ 3.30               | [Link](https://gitlab.kitware.com/cmake/cmake/-/issues/18355) |
| Ninja    | ✅ 1.11            | ✅ 1.11                 |       |
| Build2   | ✅             | ❔                 |       |
| Scons    | ❌             | ❌                 |       |
| Bazel    | ❌             | ❌                 |       |
| Meson    | ✅             | Partial            | [Link](https://github.com/mesonbuild/meson/issues/4314) |
| Gnu Make | ❌             | ❌                 |       |
| Gradle   | ❌             | ❌                 |       |

| Preprocessor | C++20 Modules | Issue |
|--------------|----------------|-------|
| Qt moc       | ❌             | [Link](https://bugreports.qt.io/browse/QTBUG-86697) |
