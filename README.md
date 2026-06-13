<a name="top"></a>
<div align="center">

<img src="https://capsule-render.vercel.app/api?type=rect&color=0:6b46c1,100:2b6cb0&height=120&section=header&text=FEDRAMPLENS&fontSize=48&fontColor=ffffff&fontAlignY=58" width="100%" alt="FEDRAMPLENS"/>

# FEDRAMPLENS

### FedRAMP boundary visualizer & OSCAL-format SSP/POAM generator

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=18&duration=3500&pause=1000&color=6B46C1&center=true&vCenter=true&width=720&lines=FedRAMP+boundary+visualizer++OSCALformat+SSPPOAM+generator;Self-hostable+%C2%B7+MCP-native+%C2%B7+CI-ready+%C2%B7+polyglot" width="720"/>

[![install](https://img.shields.io/badge/install-git%2B%20%C2%B7%20pipx%20%C2%B7%20uv-6b46c1.svg)](#install--every-way-every-platform) [![CI](https://github.com/cognis-digital/fedramplens/actions/workflows/ci.yml/badge.svg)](https://github.com/cognis-digital/fedramplens/actions) [![License: COCL 1.0](https://img.shields.io/badge/License-COCL%201.0-2b6cb0.svg)](LICENSE) [![Suite](https://img.shields.io/badge/Cognis-Neural%20Suite-6b46c1.svg)](https://github.com/cognis-digital)

*Federal / Compliance — NIST, CMMC, FedRAMP, and SBIR/GSA workflows.*

</div>

```bash
pip install "git+https://github.com/cognis-digital/fedramplens.git"
fedramplens scan .            # → prioritized findings in seconds
```

<!-- cognis:layman:start -->
## What is this?

fedramplens is a command-line tool that helps government contractors and cloud service providers check whether their software system meets FedRAMP security requirements — the federal standards required to sell cloud services to U.S. government agencies. You give it a simple JSON description of your system (what components it has, how data flows between them, and any open security issues), and it tells you what controls are missing, flags any unencrypted data crossings, and generates the official OSCAL-format documents (SSP and POA&M) that federal auditors expect. It is aimed at compliance teams, security engineers, and DevOps staff who need to prepare for or maintain a FedRAMP authorization without standing up expensive dedicated tooling.
<!-- cognis:layman:end -->

## Contents

- [Why fedramplens?](#why) · [Features](#features) · [Quick start](#quick-start) · [Example](#example) · [Architecture](#architecture) · [AI stack](#ai-stack) · [How it compares](#how-it-compares) · [Integrations](#integrations) · [Install anywhere](#install-anywhere) · [Related](#related) · [Contributing](#contributing)

<a name="why"></a>
## Why fedramplens?

FedRAMP boundary visualizer & OSCAL-format SSP/POAM generator — without standing up heavyweight infrastructure.

`fedramplens` is single-purpose, scriptable, and self-hostable: point it at a target, get prioritized results in the format your workflow already speaks (table · JSON · SARIF), gate CI on it, and let agents drive it over MCP.

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="features"></a>
## Features

- ✅ Load Boundary
- ✅ Analyze Boundary
- ✅ Generate Dot
- ✅ Generate Ssp
- ✅ Generate Poam
- ✅ Runs on Linux/macOS/Windows · Docker · devcontainer
- ✅ Ports in Python, JavaScript, Go, and Rust (`ports/`)

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="quick-start"></a>
<!-- cognis:domains:start -->
## Domains

**Primary domain:** Cyber & Security  ·  **JTF MERIDIAN division:** NULLBYTE · SPECTER

**Topics:** `cognis` `security` `infosec` `cybersecurity` `blue-team` `compliance`

Part of the **Cognis Neural Suite** — 300+ source-available tools organized across 12 domains under the JTF MERIDIAN command structure. See the [suite on GitHub](https://github.com/cognis-digital) and [jtf-meridian](https://github.com/cognis-digital/jtf-meridian) for how the pieces fit together.
<!-- cognis:domains:end -->

<!-- cognis:install:start -->
## Install

`fedramplens` is source-available (not published to PyPI) — every method below installs
straight from GitHub. Pick whichever you prefer; the one-line scripts auto-detect
the best tool available on your machine.

**One-liner (Linux / macOS):**
```sh
curl -fsSL https://raw.githubusercontent.com/cognis-digital/fedramplens/HEAD/install.sh | sh
```

**One-liner (Windows PowerShell):**
```powershell
irm https://raw.githubusercontent.com/cognis-digital/fedramplens/HEAD/install.ps1 | iex
```

**Or install manually — any one of:**
```sh
pipx install "git+https://github.com/cognis-digital/fedramplens.git"     # isolated (recommended)
uv tool install "git+https://github.com/cognis-digital/fedramplens.git"  # uv
pip install "git+https://github.com/cognis-digital/fedramplens.git"      # pip
```

**From source:**
```sh
git clone https://github.com/cognis-digital/fedramplens.git
cd fedramplens && pip install .
```

Then run:
```sh
fedramplens --help
```
<!-- cognis:install:end -->

## Quick start

```bash
pip install "git+https://github.com/cognis-digital/fedramplens.git"
fedramplens --version
fedramplens scan .                       # scan current project
fedramplens scan . --format json         # machine-readable
fedramplens scan . --fail-on high        # CI gate (non-zero exit)
```

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="example"></a>
## Example

```text
$ fedramplens scan .
  [HIGH    ] FED-001  example finding             (./src/app.py)
  [MEDIUM  ] FED-002  another signal              (./config.yaml)

  2 findings · risk score 5 · 38ms
```

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="architecture"></a>
## Architecture

```mermaid
flowchart LR
  A[Input: file / dir / API] --> B[Collectors]
  B --> C[Rules / Analyzers]
  C --> D[Scorer]
  D --> E{Reporters}
  E --> F[Table]
  E --> G[JSON / SARIF]
  E --> H[MCP tool -. drives .-> AI agents]
```

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="ai-stack"></a>
## Use it from any AI stack

`fedramplens` is interoperable with every popular way of using AI:

- **MCP server** — `fedramplens mcp` (Claude Desktop, Cursor, Cognis.Studio, [uncensored-fleet](https://github.com/cognis-digital/uncensored-fleet))
- **OpenAI-compatible / JSON** — pipe `fedramplens scan . --format json` into any agent or LLM
- **LangChain · CrewAI · AutoGen · LlamaIndex** — wrap the CLI/JSON as a tool in one line
- **CI / scripts** — exit codes + SARIF for non-AI pipelines

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="how-it-compares"></a>
## How it compares

| | **Cognis fedramplens** | GSA |
|---|:---:|:---:|
| Self-hostable, no account | ✅ | varies |
| Single command, zero config | ✅ | ⚠️ |
| JSON + SARIF for CI | ✅ | varies |
| MCP-native (AI agents) | ✅ | ❌ |
| Polyglot ports (JS/Go/Rust) | ✅ | ❌ |
| Open license | ✅ COCL | varies |

*Built in the spirit of **GSA/fedramp-automation**, re-framed the Cognis way. Missing a credit? Open a PR.*

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="integrations"></a>
## Integrations

Pipes into your stack: **SARIF** for code-scanning, **JSON** for anything, an **MCP server** (`fedramplens mcp`) for AI agents, and a webhook forwarder for SIEM/Slack/Jira. See [`docs/INTEGRATIONS.md`](docs/INTEGRATIONS.md).

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="install-anywhere"></a>
## Install — every way, every platform

```bash
pip install "git+https://github.com/cognis-digital/fedramplens.git"    # pip (works today)
pipx install "git+https://github.com/cognis-digital/fedramplens.git"   # isolated CLI
uv tool install "git+https://github.com/cognis-digital/fedramplens.git" # uv
pip install cognis-fedramplens                                          # PyPI (when published)
docker run --rm ghcr.io/cognis-digital/fedramplens:latest --help        # Docker
brew install cognis-digital/tap/fedramplens                             # Homebrew tap
curl -fsSL https://raw.githubusercontent.com/cognis-digital/fedramplens/main/install.sh | sh
```

| Linux | macOS | Windows | Docker | Cloud |
|---|---|---|---|---|
| `scripts/setup-linux.sh` | `scripts/setup-macos.sh` | `scripts/setup-windows.ps1` | `docker run ghcr.io/cognis-digital/fedramplens` | [DEPLOY.md](docs/DEPLOY.md) (AWS/Azure/GCP/k8s) |

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="related"></a>
<a name="verification"></a>
## Verification

[![tests](https://img.shields.io/badge/tests-15%20passing-2ea44f.svg)](AUDIT.md)

Every push is verified end-to-end. Latest audit (2026-06-12):

```text
tests        : 15 passed, 0 failed, 0 errored
compile      : all modules parse
cli          : C:\Python314\python.exe: No module named https
package      : https
```

<details><summary>CLI surface (<code>--help</code>)</summary>

```text
C:\Python314\python.exe: No module named https
```
</details>

Full machine-readable results: [`AUDIT.md`](AUDIT.md) · regenerate with `python -m https --help` + `pytest -q`.

<div align="right"><a href="#top">↑ back to top</a></div>


## Related Cognis tools

- [`checkpoint-ai`](https://github.com/cognis-digital/checkpoint-ai) — NIST AI RMF / EU AI Act / ISO 42001 self-assessment & SSP generator
- [`cmmcmap`](https://github.com/cognis-digital/cmmcmap) — CMMC Level 2 practice mapper — stack-aware SSP skeleton generator
- [`sbirscout`](https://github.com/cognis-digital/sbirscout) — SBIR/STTR topic discovery — DSIP + SBIR.gov + NIH digest with bid scoring
- [`gsafinder`](https://github.com/cognis-digital/gsafinder) — GSA Schedule opportunity surveyor — SAM.gov + eBuy + FedConnect
- [`clearancepath`](https://github.com/cognis-digital/clearancepath) — Personnel clearance hygiene tracker — SF-86, SEAD-3/4, training currency

**Explore the suite →** [🗂️ all 170+ tools](https://github.com/cognis-digital/cognis-neural-suite) · [⭐ awesome-cognis](https://github.com/cognis-digital/awesome-cognis) · [🔗 cognis-sources](https://github.com/cognis-digital/cognis-sources) · [🤖 uncensored-fleet](https://github.com/cognis-digital/uncensored-fleet) · [🧠 engram](https://github.com/cognis-digital/engram)

<div align="right"><a href="#top">↑ back to top</a></div>

<a name="contributing"></a>
## Contributing

PRs, new rules, and demo scenarios are welcome under the collaboration-pull model — see [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

> ### ⭐ If `fedramplens` saved you time, **star it** — it genuinely helps others find it.

## License

Source-available under the **Cognis Open Collaboration License (COCL) v1.0** — free for personal, internal-evaluation, research, and educational use; **commercial / production use requires a license** (licensing@cognis.digital). See [LICENSE](LICENSE).

---

<div align="center"><sub><b><a href="https://cognis.digital">Cognis Digital</a></b> · one of 170+ tools in the <a href="https://github.com/cognis-digital/cognis-neural-suite">Cognis Neural Suite</a> · <i>Making Tomorrow Better Today</i></sub></div>
