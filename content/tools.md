
## Compiler

| Compiler     | C++20 Modules     | C++23 Standard Library Modules  `import std;` |
|--------------|-------------------|--------------------|
| MSVC 2022    | ✅ (17.6)          | ✅ (17.10)       | 
| Clang        | Partial (17)      | Partial (18)       | 
| Apple Clang  | ❌                | ❌                | 
| GCC          | Partial (14)      | ❌                | 

# Build Tools

| Tool     | C++20 Modules | C++23 Standard Library Modules  `import std;` | Info |
|----------|----------------|--------------------|-------|
| CMake    | ✅ 3.28             | ✅ 3.30               | [Issue Link](https://gitlab.kitware.com/cmake/cmake/-/issues/18355) |
| Ninja    | ✅ 1.11            | ✅ 1.11                 |       |
| Build2   | ✅             | Partial (0.17.0-stage) msvc and clang-with-libc++ only | [Issue Link](https://github.com/build2/build2/issues/333) |
| Scons    | ❌             | ❌                 |       |
| Bazel    | ❌             | ❌                 | [Issue Link](https://github.com/bazelbuild/bazel/issues/4005)      |
| Meson    | ✅             | Partial            | [Issue Link](https://github.com/mesonbuild/meson/issues/4314) |
| Gnu Make | ✅             | ❌                 | [Demo Project](https://github.com/fvilante/cpp20_modules_with_gcc_demo)      |
| Gradle   | ❌             | ❌                 |       |
| qmake   | ❌             | ❌                 |   Deprecated and shout  no longer be used!    |
| qbs   | ❌             | ❌                 |   [Issue Link](https://bugreports.qt.io/browse/QBS-1181)   |
| XMake   | ✅            | ✅                |    |

## Exotic Tools and Preprocessor

| Preprocessor | C++20 Modules | Description      | Issue | 
|--------------|---------------|-----------------|-------|
| Qt moc       | ❌           | Qt needs to add modules support to their preprocessor before they can even begin adding modules support. The last conversation happened mid December 2023 [here](https://lists.qt-project.org/pipermail/development/2023-December/044800.html).  fabiankosmale [laid out the challenges for this](https://lists.qt-project.org/pipermail/development/2023-December/044802.html), but no timeline was given for when it will be done. | [Link](https://bugreports.qt.io/browse/QTBUG-86697) |
