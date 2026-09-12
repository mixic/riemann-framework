# Riemann Framework

Ein Forschungs-Framework zur **formalen und numerischen Verifikation** von Beweisversuchen der Riemannschen Hypothese (RH).

## Disclaimer

Dieses Projekt ist **kein Beweis** der Riemannschen Hypothese. Es ist ein Werkzeug, um:
- die RH **numerisch** für bekannte Nullstellen zu testen,
- **formale Beweisversuche** in Lean 4 zu verifizieren,
- die **explizite Formel** zu visualisieren und zu analysieren.

Ein bestandener Test ist **Evidenz**, kein mathematischer Beweis.

## Ziel

Die Riemannsche Hypothese besagt, dass alle nicht-trivialen Nullstellen der
Riemannschen Zeta-Funktion auf der kritischen Linie `Re(s) = 1/2` liegen.

Dieses Framework kombiniert:
- **Python** (mpmath, numpy, matplotlib) für numerische Verifikation und Visualisierung,
- **Lean 4 + Mathlib** für formale Verifikation von Beweisversuchen,
- **pytest** als Test-Infrastruktur (Unit-Test-Metapher für die RH).

## 📁 Projektstruktur

```
riemann-framework/
│
├── README.md                     # Hauptdokumentation
├── LICENSE                       # z. B. MIT
├── .gitignore                    # Python, Lean, VS Code ausschließen
├── lakefile.toml                 # Lean 4 Projektdefinition
├── lean-toolchain                # Lean-Version (z. B. leanprover/lean4:v4.x.x)
│
├── lean/                         # Formale Verifikation
│   └── RiemannFramework/
│       ├── RiemannHypothesis.lean    # RH als Theorem mit `sorry`
│       ├── Basic.lean                # Definitionen (IsNontrivialZero, etc.)
│       └── SanityChecks.lean         # Tests der Definitionen
│
├── python/                       # Numerische Tests und Steuerung
│   ├── pyproject.toml            # Projektdefinition (uv/pip)
│   ├── requirements.txt          # numpy, matplotlib, mpmath, pytest
│   │
│   ├── riemann_framework/
│   │   ├── __init__.py
│   │   ├── zeta.py               # mpmath-Wrapper für ζ(s)
│   │   ├── zeros.py              # Berechnung / Verifikation von Nullstellen
│   │   ├── explicit_formula.py   # Riemannsche explizite Formel
│   │   ├── lean_runner.py        # Kompiliert Lean-Dateien via subprocess
│   │   └── plots.py              # Grafiken erzeugen
│   │
│   └── tests/
│       ├── test_numeric_zeros.py     # Numerischer Assert
│       ├── test_formal_proof.py      # Formaler Assert (Lean)
│       └── test_explicit_formula.py  # Test der expliziten Formel
│
├── scripts/                      # Hilfsskripte
│   ├── setup_lean.sh             # Lean + Mathlib einrichten
│   └── generate_plots.py         # Alle Grafiken auf einmal
│
├── docs/                         # Dokumentation
│   ├── research_notes.md         # Was bisher versucht wurde
│   ├── number_systems.md         # Deine Idee mit neuen Zahlensystemen
│   └── verification.md           # Wie ein RH-Beweis geprüft wird
│
├── output/                       # Generierte Grafiken (in .gitignore)
│   └── .gitkeep
│
└── .github/
    └── workflows/
        └── ci.yml                # GitHub Actions: Tests automatisch ausführen
```

## Lizenz

Dieses Projekt steht unter der **GNU General Public License v3.0**.

Siehe [`LICENSE`](LICENSE) für den vollständigen Text.

**Hinweis:** Die verwendete Lean-Bibliothek **Mathlib** steht unter der
Apache License 2.0 und ist mit GPL v3 kompatibel. Siehe
[Mathlib LICENSE](https://github.com/leanprover-community/mathlib4/blob/master/LICENSE).