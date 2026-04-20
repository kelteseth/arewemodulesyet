## Compilers

| Compiler     | C++20 Modules     | Info |
|--------------|-------------------|------|
| MSVC 2022    | ✅ (17.6)          |      |
| Clang        | ✅  (22)      |      |
| Apple Clang  | ❌                |      |
| GCC          | ✅  (15)      |      |

## Standard Libraries

| Standard Library | Provides `import std;` | Info |
|------------------|------------------------|------|
| MSSTL            | ✅ (17.10)             |      |
| libc++           | ✅ (18)           |      |
| libstdc++        | ✅ (15)       |      |

## Build Tools

| Tool          | C++20 Modules | `import std;` | Header Units | Info |
|---------------|---------------|---------------|--------------|------|
| Ninja         | ✅ 1.11       | ✅ 1.11       | ❌           |      |
| MSBuild       | ✅            | ✅            | ❌           |      |
| CMake         | ✅ 3.28       | ✅ 3.30       | ❌           | [Issue Link](https://gitlab.kitware.com/cmake/cmake/-/issues/18355) |
| XMake         | ✅            | ✅            | ✅           | [Release](https://github.com/xmake-io/xmake/wiki/Xmake-v2.7.1-Released,-Better-Cplusplus-Modules-Support) |
| Zork++        | ✅            | ✅            | ❌           | [Project](https://github.com/zerodaycode/Zork) |
| Build2        | ✅            | ✅ 0.17.0     | ❌           | [Issue Link](https://github.com/build2/build2/issues/333) |
| qbs           | ✅ 2.5        | ✅ 3.1        | ❌           | [Tutorial](https://qbs.io//docs/tutorial-10/) |
| Meson         | Partial       | ❌            | ❌           | [Issue Link](https://github.com/mesonbuild/meson/issues/5024) |
| Gnu Make      | ✅            | ❌            | ❌           | [Demo Project](https://github.com/fvilante/cpp20_modules_with_gcc_demo) |
| Cabin         | ❌            | ❌            | ❌           |      |
| HMake         | ✅            | ✅            | ✅           |      |
| GNU Autotools | ❌            | ❌            | ❌           |      |
| Scons         | ⚙️            | ❌            | ❌           | [PR for GCC support](https://github.com/SCons/scons/pull/4248) |
| ccache        | ⚙️            | ❌            | ❌           | [PR](https://github.com/ccache/ccache/pull/1523) |
| sccache       | ⚙️            | ❌            | ❌           | [PR (clang)](https://github.com/mozilla/sccache/pull/2516) |
| Bazel         | ✅            | ⚙️            | ❌           | [Issue Link](https://github.com/bazelbuild/bazel/issues/4005) |
| Gradle        | ❌            | ❌            | ❌           | [Issue Link](https://github.com/gradle/gradle/issues/29009) |
| fastbuild     | ❌            | ❌            | ❌           | [Issue Link](https://github.com/fastbuild/fastbuild/issues/1026) |
| qmake         | ❌            | ❌            | ❌           | 💀 Deprecated and should no longer be used! |

## Language Server (IDE Support)

| Tool               | C++20 Modules | Info |
|--------------------|---------------|------|
| Clangd             | ✅  | [C++20 Modules in clangd](https://chuanqixu9.github.io/c++/2025/12/03/Clangd-support-for-Modules.en.html) |
| vscode-cmake-tools | ❌            | [Issue Link](https://github.com/microsoft/vscode-cmake-tools/issues/3335) |

## Static analyzers

| Tool          | C++20 Modules      | `import std;` | Header Units | Info |
|---------------|--------------------|---------------|--------------|------|
| Sonar         | Experimental       | ✅            | ❌          | [Modules documentation](https://docs.sonarsource.com/sonarqube-cloud/analyzing-source-code/languages/c-family/customizing-the-analysis#cpp-20-modules) | 

## Preprocessor

| Tool   | C++20 Modules | Info |
|--------|---------------|------|
| Qt moc | ❌            | Qt needs to add modules support to their preprocessor before they can even begin adding modules support. The last conversation happened mid December 2023 [here](https://lists.qt-project.org/pipermail/development/2023-December/044800.html). fabiankosmale [laid out the challenges for this](https://lists.qt-project.org/pipermail/development/2023-December/044802.html), but no timeline was given for when it will be done. [Link](https://bugreports.qt.io/browse/QTBUG-86697) |
