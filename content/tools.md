
## Compiler

| Compiler     | C++20 Modules     |
|--------------|-------------------|
| MSVC 2022    | ✅ (17.6)          |
| Clang        | Partial (17)      |
| Apple Clang  | ❌                |
| GCC          | Partial (14)      |

## Standard Libaries

| Standard Library | Provides `import std;` |
|--------------|--------------------|
| MSSTL    | ✅ (17.10)       |
| libc++        | Partial (18)       |
| libstdc++          | ❌                |

# Build Tools

| Tool     | C++20 Modules | C++23 Standard Library Modules  `import std;` | Info |
|----------|----------------|--------------------|-------|
| Ninja    | ✅ 1.11            | ✅ 1.11                 |       |
| MSBuild   | ✅            | ✅                |  |
| CMake    | ✅ 3.28             | ✅ 3.30               | [Issue Link](https://gitlab.kitware.com/cmake/cmake/-/issues/18355) |
| XMake   | ✅            | ✅                |   [Release](https://github.com/xmake-io/xmake/wiki/Xmake-v2.7.1-Released,-Better-Cplusplus-Modules-Support) |
| Zork++   | ✅            | ✅                |   [Project](https://github.com/zerodaycode/Zork) |
| Build2   | ✅             | ✅ 0.17.0 | [Issue Link](https://github.com/build2/build2/issues/333) |
| Meson    | Partial            | ❌            | [Issue Link](https://github.com/mesonbuild/meson/issues/5024) |
| Gnu Make | ✅             | ❌                 | [Demo Project](https://github.com/fvilante/cpp20_modules_with_gcc_demo)      |
| qbs      | ✅             | ❌                 | [Blog Post](https://www.qt.io/blog/qbs-2.5-released) |
| Scons    | ⚙️             | ❌                 |  [PR for GCC support](https://github.com/SCons/scons/projects/14#card-86356523)     |
| ccache     | ❌             | ❌                 | [Issue Link](https://github.com/ccache/ccache/issues/1252)      |
| sccache     | ❌             | ❌                 | [Issue Link](https://github.com/mozilla/sccache/issues/2095)      |
| Bazel    | ❌             | ❌                 | [Issue Link](https://github.com/bazelbuild/bazel/issues/4005)      |
| Gradle   | ❌             | ❌                 |  [Issue Link](https://github.com/gradle/gradle/issues/29009)     |
| fastbuild   | ❌             | ❌                 |  [Issue Link](https://github.com/fastbuild/fastbuild/issues/1026)   |
| qmake   | ❌             | ❌                 |  💀 Deprecated and should no   longer be used!    |


## Language Server (IDE Support)

| Preprocessor | C++20 Modules | Description      | Issue |
|--------------|---------------|-----------------|-------|
| Clangd       | ❌  (maybe clang 19)         |   | [Issue Link](https://github.com/clangd/clangd/issues/1293) [PR](https://github.com/llvm/llvm-project/pull/66462#issuecomment-1950743841)|
| clangd (forked) | ✅  | need to be built from source | [Repo Link](https://github.com/ChuanqiXu9/clangd-for-modules) |
| vscode-cmake-tools        | ❌          |   | [Issue Link](https://github.com/microsoft/vscode-cmake-tools/issues/3335) |


## Preprocessor

| Preprocessor | C++20 Modules | Description      | Issue |
|--------------|---------------|-----------------|-------|
| Qt moc       | ❌           | Qt needs to add modules support to their preprocessor before they can even begin adding modules support. The last conversation happened mid December 2023 [here](https://lists.qt-project.org/pipermail/development/2023-December/044800.html).  fabiankosmale [laid out the challenges for this](https://lists.qt-project.org/pipermail/development/2023-December/044802.html), but no timeline was given for when it will be done. | [Link](https://bugreports.qt.io/browse/QTBUG-86697) |
