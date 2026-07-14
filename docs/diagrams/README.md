<!-- docs>diagrams>README.md -->

# Diagrams

This directory contains the UML diagrams used to document the architecture and design of AskMyData.

All diagrams are written in **PlantUML** to ensure they remain:

- version-controlled;
- easy to review;
- maintainable;
- synchronized with the project documentation.

Generated SVG files are committed to the repository for easy viewing on GitHub.

---

# Diagram Overview

| PlantUML Source | Generated Diagram | Description |
|---|---|---|
| `src/system-context.puml` | `generated/AskMyData_System_Context.svg` | System context diagram showing AskMyData, its users and external systems. |
| `src/system-use-cases.puml` | `generated/AskMyData_System_Use_Cases.svg` | UML use case diagram describing the main user interactions with the system. |
| `src/domain-model.puml` | `generated/AskMyData_Domain_Model.svg` | UML class diagram representing the main domain entities, relationships and cardinalities. |
| `src/application-components.puml` | `generated/AskMyData_Application_Components.svg` | High-level application architecture showing the main modules, dependencies and infrastructure components. |

---

# Diagram Organization

Each diagram documents a different architectural viewpoint.

| Diagram | Purpose |
|---|---|
| **System Context** | Defines the system boundaries and external actors. |
| **System Use Cases** | Describes the main business capabilities available to users. |
| **Domain Model** | Represents the business domain independently from implementation details. |
| **Application Components** | Describes the internal modular architecture of the application. |

Together, these diagrams provide a consistent overview of the project from business requirements to software architecture.

---

# Rendering

The diagrams can be rendered using:

- the PlantUML extension for Visual Studio Code;
- the PlantUML command-line tool;
- an online PlantUML server.

SVG format is recommended for documentation committed to the repository.

---

# Update Guidelines

Whenever a PlantUML source file is modified:

1. regenerate the corresponding SVG diagram;
2. commit both the `.puml` source and the generated `.svg`;
3. ensure the diagram remains consistent with the associated documentation.

The PlantUML source is the reference artifact.
Generated SVG files are derived documentation.