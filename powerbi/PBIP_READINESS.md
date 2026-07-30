# PBIP Readiness

The repository contains source-controlled assets needed to build and then save a Power BI Project:

- Typed Power Query definitions for all CSV exports.
- A complete DAX measure layer and measure dictionary.
- A validated relationship and table manifest.
- A report theme and six-page visual specification.
- Manual validation, accessibility, and deployment checklists.

It intentionally does not contain a hand-authored `.pbip`, Report definition, or SemanticModel definition. Power BI Projects and TMDL storage remain preview/developer-mode features, and Microsoft documents Power BI Desktop as the supported creator and converter. Some report and diagram files do not support external editing; invalid external edits can prevent Desktop from opening the project.

Official references:

- [Power BI Desktop projects overview](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview)
- [Power BI project semantic model folder](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset)
- [Power BI project report folder](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report)

After completing and validating `BUILD_POWERBI.md`, use Power BI Desktop **File > Save As > Power BI Project (.pbip)** with TMDL storage enabled. Reopen the saved project before committing it to source control.
