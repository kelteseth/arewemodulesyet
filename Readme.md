# Are we modules yet? Not even close, lol.

This website tracks C++20 modules support across popular libraries using vcpkg port revision counts to estimate popularity.

## How Projects Are Counted

**Total C++ Projects:**
```
  vcpkg packages (baseline)
- Excluded C libraries (pure C, can't use modules)
+ External projects (notable C++ projects not in vcpkg)
= Total C++ projects tracked
```

**Completed Projects (with modules support):**
```
  vcpkg packages with ✅ status (from vcpkg_overrides.yml)
+ External projects with ✅ status (from external_projects.yml)
= Total completed
```

> **Note:** Only packages that exist in vcpkg can be overridden via `vcpkg_overrides.yml`. 
> Projects not in vcpkg must be added to `external_projects.yml`.

## Data Files

**Auto-generated** (`data/generated/` - DO NOT EDIT):
- `vcpkg_packages.yml` - Generated from vcpkg repository

**Manual** (`data/`):
- `vcpkg_overrides.yml` - Override vcpkg package metadata (must exist in vcpkg)
- `external_projects.yml` - Projects not in vcpkg
- `excluded_c_libraries.yml` - C libraries to exclude from tracking

**Output** (`data/`):
- `progress.yml` - Merged result displayed on website

## YAML Fields

Example entry in `vcpkg_overrides.yml`:
```yml
ports:
- name: fmt
  import_statement: fmt              # Module import name (e.g., `import fmt;`)
  modules_support_date: 2022-10-11   # Date modules added (ISO 8601: YYYY-MM-DD)
  status: ✅
  current_min_cpp_version: 11
  tracking_issue: "https://github.com/fmtlib/fmt/pull/3134"
```

Note: Most projects don't have a modules tracking issue. If one doesn't exist, please create one so we can track it here.

### Status Legend
- ❔ Unknown - Help wanted!
- ✅ Full support
- ⚙️ Work in progress
- ⚠️ Issue reported
- ❌ No support planned

## Dependencies
1. [Hugo Extended](https://gohugo.io/)
   - 🪟 `winget install Hugo.Hugo.Extended`
   - 🐧🍏 [GitHub releases](https://github.com/gohugoio/hugo/releases)
2. [Python 3 via uv](https://docs.astral.sh/uv/)
   - 🪟 `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
   - 🐧🍏 `curl -LsSf https://astral.sh/uv/install.sh | sh`

## Contributing

**Edit vcpkg package status:** `data/vcpkg_overrides.yml`  
**Add external projects:** `data/external_projects.yml`

Generate merged data:
```bash
uv run tools/merge_vcpkg_package_list_progress.py
uv run tools/compute_completion_status.py
hugo serve  # Preview changes
```

**Regenerate vcpkg data (optional):**
```bash
uv run tools/generate_vcpkg_package_list.py
```

## Project Structure
```
data/
├── vcpkg_overrides.yml       # Manual: vcpkg package overrides
├── external_projects.yml     # Manual: non-vcpkg projects
├── excluded_c_libraries.yml  # Manual: C libraries to exclude
├── progress.yml              # Output: merged result for website
└── generated/
    └── vcpkg_packages.yml    # Auto-generated from vcpkg (DO NOT EDIT)
tools/
├── generate_vcpkg_package_list.py      # Fetches vcpkg data
├── merge_vcpkg_package_list_progress.py # Merges all data → progress.yml
└── compute_completion_status.py        # Generates historical stats
layouts/partials/
├── progress-table.html       # Table component
├── progress-plot.html        # Chart component
└── home-content.html         # Home page content
content/
├── tools.md
├── documents.md
└── examples.md
```
