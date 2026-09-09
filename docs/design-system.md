# AskMyData Design System

## 1. Purpose

This document defines the visual foundations and UI conventions of AskMyData.

It serves as the reference for maintaining visual consistency between:

- wireframes;
- mockups;
- prototypes;
- frontend implementation.

The corresponding visual styles, variables, and components are maintained in Figma.

This document is expected to evolve as the product and its interface are refined.

---

## 2. Design Principles

AskMyData is a data exploration application designed to make structured data accessible through a simple and understandable interface.

The interface should reflect the following principles.

### 2.1 Simple

The interface should reduce unnecessary complexity and expose technical information only when it is useful to the user.

### 2.2 Professional

The visual language should be appropriate for a professional data application.

Decorative elements should remain restrained.

### 2.3 Data-oriented

The interface should communicate reliability, structure, and clarity.

Information hierarchy should remain immediately understandable, including on screens containing technical metadata.

### 2.4 Accessible

The application should remain understandable for users who are not data or software specialists.

Technical concepts should not dominate the interface when they are not required for the user's task.

### 2.5 Consistent

Repeated actions, states, navigation elements, and information structures should use consistent visual patterns throughout the application.

### 2.6 AI as a capability, not a visual theme

Artificial intelligence is part of the application's functionality but should not dictate the entire visual identity.

The interface should avoid stereotypical "AI" aesthetics such as excessive gradients, glowing effects, or highly decorative futuristic elements.

---

# 3. Visual Identity

## 3.1 General Direction

The visual direction of AskMyData is:

- modern;
- minimal;
- professional;
- data-oriented;
- technology-oriented;
- predominantly light;
- based on neutral surfaces with restrained use of the brand color.

The interface should resemble a professional SaaS/data product rather than a promotional AI product.

---

## 3.2 Brand Color

The main brand color is a teal / blue-green.

### Primary

| Token | Value |
|---|---|
| Primary 500 | `#1AA79E` |

`Primary 500` is the reference brand color of AskMyData.

It may be used for:

- primary actions;
- active navigation elements;
- selected elements;
- links;
- focus indicators;
- selected tabs;
- key interface accents.

The brand color should not be used as the dominant background color of the application.

---

## 3.3 Primary Color Scale

The following scale provides lighter and darker variants of the brand color.

| Token | Value | Typical usage |
|---|---|---|
| Primary 50 | `#F0FDFA` | Subtle tinted backgrounds |
| Primary 100 | `#CCFBF1` | Light selected states |
| Primary 200 | `#99F6E4` | Light accents |
| Primary 300 | `#5EEAD4` | Secondary accents |
| Primary 400 | `#2DD4BF` | Strong accents |
| Primary 500 | `#1AA79E` | Brand color |
| Primary 600 | `#0F8F87` | Primary controls / stronger contrast |
| Primary 700 | `#0F766E` | Hover / active states |
| Primary 800 | `#115E59` | High-contrast teal |
| Primary 900 | `#134E4A` | Dark teal |

The scale may be adjusted during mockup creation if contrast testing or visual evaluation requires it.

---

# 4. Neutral Colors

AskMyData uses a cool neutral palette based on slate tones.

| Token | Value | Typical usage |
|---|---|---|
| Neutral 50 | `#F8FAFC` | Page background |
| Neutral 100 | `#F1F5F9` | Secondary backgrounds |
| Neutral 200 | `#E2E8F0` | Borders and separators |
| Neutral 300 | `#CBD5E1` | Disabled borders / stronger separators |
| Neutral 500 | `#64748B` | Secondary text |
| Neutral 700 | `#334155` | Strong secondary text |
| Neutral 950 | `#0F172A` | Primary text |
| White | `#FFFFFF` | Main surfaces |

### Default usage

| Element | Color |
|---|---|
| Application background | Neutral 50 |
| Main surfaces | White |
| Cards | White |
| Primary text | Neutral 950 |
| Secondary text | Neutral 500 |
| Borders | Neutral 200 |

The interface should primarily use neutral colors.

The primary teal color should be reserved for elements requiring emphasis or interaction.

---

# 5. Semantic Colors

Semantic colors communicate application states independently from the brand color.

The system must provide four semantic categories:

- Success;
- Warning;
- Error;
- Info.

Exact color values will be validated during mockup creation and accessibility testing.

Semantic colors may be used for states such as:

### Data Source

- Connected;
- Connecting;
- Disconnected;
- Error.

### Catalog

- Ready;
- Building;
- Regenerating;
- Outdated;
- Error.

### General Operations

- Success;
- In progress;
- Warning;
- Failure.

Color must never be the only way to communicate a state.

A state should normally combine:

- text;
- color;
- and, when useful, an icon.

Example:

`✓ Connected`

rather than a green indicator without a textual label.

---

# 6. Typography

## 6.1 Font Family

AskMyData uses:

**Inter**

Inter is used throughout the interface.

A second typeface is not required.

---

## 6.2 Typography Scale

Initial typography scale:

| Style | Size | Weight | Typical usage |
|---|---:|---:|---|
| Display | 32 px | 600 | Major page or onboarding titles |
| H1 | 28 px | 600 | Page titles |
| H2 | 24 px | 600 | Major sections |
| H3 | 20 px | 600 | Cards / subsections |
| Body | 16 px | 400 | Standard content |
| Body Medium | 16 px | 500 | Emphasized content |
| Body Small | 14 px | 400 | Secondary information |
| Label | 14 px | 500 | Form and UI labels |
| Caption | 12 px | 400 | Metadata and supporting information |

The final type scale may be refined during mockup creation.

---

## 6.3 Typography Principles

Typography should establish hierarchy without relying excessively on font size.

Prefer differences in:

- weight;
- spacing;
- position;
- text color;

before introducing unnecessary additional font sizes.

Long text should use comfortable line heights and should not be compressed into dense blocks.

---

# 7. Spacing

## 7.1 Base Unit

The spacing system uses a **4 px base unit**.

Preferred spacing values:

| Token | Value |
|---|---:|
| Space 1 | 4 px |
| Space 2 | 8 px |
| Space 3 | 12 px |
| Space 4 | 16 px |
| Space 5 | 20 px |
| Space 6 | 24 px |
| Space 8 | 32 px |
| Space 10 | 40 px |
| Space 12 | 48 px |
| Space 16 | 64 px |

Multiples of 8 px should be preferred for major layout spacing.

4 px and 12 px may be used for finer internal spacing.

---

## 7.2 Initial Usage Guidelines

Typical starting values:

| Element | Spacing |
|---|---:|
| Small icon/text gap | 8 px |
| Related elements | 8–12 px |
| Form fields | 16 px |
| Card padding | 24 px |
| Section spacing | 32 px |
| Main page padding | 32 px |

These values provide defaults rather than strict constraints.

---

# 8. Border Radius

AskMyData uses moderately rounded corners.

The interface should avoid both completely sharp geometry and excessively rounded "pill" styling.

| Token | Value |
|---|---:|
| Radius XS | 4 px |
| Radius SM | 6 px |
| Radius MD | 8 px |
| Radius LG | 12 px |
| Radius XL | 16 px |

### Initial component usage

| Component | Radius |
|---|---:|
| Button | 8 px |
| Input | 8 px |
| Select | 8 px |
| Card | 12 px |
| Badge | 6 px |
| Modal | 16 px |

Pill-shaped components should only be used when their semantics justify that shape.

---

# 9. Borders

Borders should remain subtle.

Default border:

```text
1 px solid Neutral 200
```

Borders may be used for:

- cards;
- form controls;
- panels;
- separators;
- tables;
- dialogs;
- dropdowns.

Heavy borders should generally be avoided.

---

# 10. Shadows

Shadows should be used sparingly.

Standard content cards should normally rely on borders rather than shadows.

Example:

```text
Card
Background: White
Border: 1 px Neutral 200
Shadow: None
```

Shadows may be introduced for elements that visually sit above the interface, such as:

- dropdowns;
- popovers;
- menus;
- dialogs;
- modals.

Exact shadow tokens will be defined during mockup creation.

---

# 11. Icons

## 11.1 Icon Library

AskMyData uses:

**Lucide**

Icons should use a consistent stroke style and visual weight.

---

## 11.2 Icon Usage

Icons should support comprehension rather than act as decoration.

Potential navigation mappings include:

| Concept | Icon |
|---|---|
| Dashboard | LayoutDashboard |
| Project | Folder |
| Data | Database |
| Conversation | MessageSquare |
| Settings | Settings |
| Refresh | RefreshCw |
| Delete | Trash2 |
| More actions | Ellipsis |
| Previous | ArrowLeft |
| Next | ArrowRight |

Exact icons may be adjusted during mockup creation.

Icons should normally be accompanied by text when the action may not be immediately obvious.

---

# 12. Layout

## 12.1 General Structure

The desktop application uses a persistent sidebar and a main content area.

Typical structure:

```text
┌──────────────┬─────────────────────────────────────┐
│              │                                     │
│   Sidebar    │             Main Content            │
│              │                                     │
│              │                                     │
└──────────────┴─────────────────────────────────────┘
```

The sidebar provides global and project-level navigation.

The main content area contains the current page.

---

## 12.2 Main Content

Main content should:

- maintain consistent horizontal alignment between pages;
- use predictable page padding;
- preserve clear hierarchy between page header and content;
- avoid unnecessarily wide text blocks.

Detailed responsive behavior will be defined when frontend implementation requirements are established.

---

# 13. Navigation

The interface currently distinguishes two navigation contexts.

## 13.1 Global Context

Used when the user is outside a specific project.

Examples:

- Dashboard;
- Create Project.

## 13.2 Project Context

Used when a project is open.

The active project should be clearly identified in the sidebar.

Project-level navigation currently includes:

- Conversation;
- Data;
- Settings.

The active page must be visually distinguishable.

Primary color may be used as part of the active state, but should not be the only indicator.

---

# 14. Buttons

The initial design system should support at least:

- Primary Button;
- Secondary Button;
- Destructive Button;
- Icon Button.

## 14.1 Primary Button

Used for the main action of a screen or section.

Examples:

- Create Project;
- Next;
- Build Catalog;
- Send.

Typical styling:

```text
Background: Primary
Text: White
Border: Primary
Radius: 8 px
```

Only one visually dominant primary action should normally exist within the same action group.

---

## 14.2 Secondary Button

Used for secondary actions.

Examples:

- Previous;
- Cancel;
- Settings;
- Test Connection.

Typical styling:

```text
Background: White
Text: Neutral 950
Border: Neutral 300
Radius: 8 px
```

---

## 14.3 Destructive Button

Used for destructive actions.

Example:

- Delete Project.

It should use the semantic Error color rather than the brand color.

---

## 14.4 Icon Button

Used for compact actions where the icon is sufficiently recognizable.

Example:

- project card menu.

Icon buttons must have an accessible label in the implemented application.

---

## 14.5 Button States

Buttons should eventually define:

- Default;
- Hover;
- Active;
- Focus;
- Disabled;
- Loading.

Exact visual states will be specified during mockup creation.

---

# 15. Form Controls

The design system should support:

- Text Input;
- Text Area;
- Select;
- Checkbox;
- Radio Button;
- Password Input.

Each form field should provide:

- a visible label;
- the control;
- optional supporting text;
- validation feedback when required.

Placeholder text should not replace the field label.

---

## 15.1 Form States

Form controls should support:

- Default;
- Hover;
- Focus;
- Filled;
- Disabled;
- Error;
- Success when relevant.

Focus states should use a clearly visible indicator associated with the Primary color.

---

# 16. Cards and Panels

Cards should organize related information without unnecessarily fragmenting the interface.

Default card:

```text
Background: White
Border: Neutral 200
Radius: 12 px
Shadow: None
Padding: 24 px
```

Potential card types include:

- Project Card;
- Settings Section;
- Data Summary;
- Status Panel.

Cards should not be introduced when simple spacing and hierarchy are sufficient.

---

# 17. Badges and Status Indicators

Badges may represent:

- project status;
- catalog status;
- connection status;
- processing state.

Existing or expected states include examples such as:

- Draft;
- Configuring;
- Building Catalog;
- Ready;
- Regenerating Catalog;
- Archived.

Badge appearance should be based on semantic meaning rather than assigning arbitrary colors to every state.

Badges should always contain readable text.

---

# 18. Tabs

Tabs are used to switch between closely related views within the same page.

Current example:

```text
Data

Overview    Schema
```

The active tab should be identifiable through more than color alone.

A combination of:

- stronger text weight;
- Primary color;
- underline or indicator;

may be used.

Tabs should not replace primary application navigation.

---

# 19. Data Presentation

AskMyData contains interfaces for exploring structured data and metadata.

Data presentation should prioritize:

1. readability;
2. hierarchy;
3. relationships;
4. useful context;
5. progressive disclosure of technical details.

Technical information should be available when useful without overwhelming non-technical users.

Potential structures include:

- key/value information;
- tables;
- schema lists;
- relationship views;
- catalog summaries;
- metadata panels.

Exact visualization patterns will be refined as the underlying data catalog implementation is developed.

---

# 20. Conversational Interface

Conversation is one of the primary interfaces of AskMyData.

The interface should clearly distinguish:

- user messages;
- assistant messages;
- system/process information when necessary.

Responses should prioritize the natural-language answer.

Technical execution details should remain secondary and should not dominate the standard user experience.

The interface should accommodate the fact that answering one natural-language question may involve multiple internal processing steps or database queries.

Internal SQL execution should therefore not be presented as if every user question necessarily maps to a single SQL query.

Detailed technical traces, if implemented, should be treated as secondary or debugging information.

---

# 21. Feedback and System States

The application must communicate operations that may take time.

Examples include:

- testing a database connection;
- reading database schemas;
- generating metadata;
- building the catalog;
- regenerating the catalog;
- creating a project.

Relevant feedback patterns may include:

- loading indicators;
- progress indicators;
- status text;
- success messages;
- error messages.

The amount of feedback should reflect the duration and importance of the operation.

---

# 22. Accessibility

Accessibility should be considered from the beginning of the design process.

## 22.1 Contrast

Text and interactive elements should meet WCAG contrast requirements.

The final Primary scale and semantic colors must be tested against their intended backgrounds before implementation.

---

## 22.2 Color

Color must not be the sole carrier of information.

For example:

```text
✓ Connected
```

is preferable to:

```text
●
```

where the state can only be understood from the dot color.

---

## 22.3 Focus

Interactive elements must provide a clearly visible keyboard focus state.

---

## 22.4 Labels

Inputs and controls must have explicit labels.

Icon-only controls must receive accessible names during implementation.

---

## 22.5 Interactive Targets

Buttons and other interactive controls should provide sufficiently large clickable areas.

---

# 23. Responsive Design

AskMyData primarily targets desktop usage.

The interface should adapt to different desktop screen sizes, from laptop displays to larger monitors, while preserving access to all core features.

Responsive behavior should account for:

- available viewport width;
- information density;
- navigation usability;
- component resizing and wrapping;
- preservation of core actions and content.

The MVP does not require mobile-specific navigation, mobile-optimized layouts or tablet-specific designs.

Exact breakpoints and component-level responsive rules will be refined during frontend implementation.

---

# 24. Figma Organization

The Figma file currently separates the design process into dedicated pages.

The Design System page should contain reusable visual foundations and components.

Recommended organization:

```text
03 - Design System

Foundations
├── Colors
├── Typography
├── Spacing
├── Radius
└── Effects

Components
├── Buttons
├── Inputs
├── Selects
├── Checkboxes
├── Radio Buttons
├── Badges
├── Tabs
├── Cards
├── Navigation
└── Feedback
```

Reusable components should use Figma components and variants where useful.

Variables should be preferred for reusable design tokens when supported by the current Figma plan and workflow.

---

# 25. Design Tokens

Design values should progressively be represented as reusable tokens rather than hard-coded independently into components.

Initial token categories:

```text
color.primary.*
color.neutral.*
color.semantic.*

text.*

space.*

radius.*

border.*

shadow.*
```

The naming convention may evolve when the frontend architecture is defined.

The conceptual meaning of tokens should remain consistent between Figma and the application.

---

# 26. Source of Truth

The design system is maintained across two complementary sources.

## Documentation

`docs/design-system.md`

Defines:

- design principles;
- visual conventions;
- rationale;
- usage rules;
- agreed design decisions.

## Figma

`03 - Design System`

Defines:

- visual styles;
- variables;
- component implementations;
- variants;
- interaction states.

When a significant design decision changes, both sources should be updated when relevant.

---

# 27. Current Status

The following foundations are currently defined:

- visual direction;
- Primary brand color;
- neutral color direction;
- typography family;
- initial typography scale;
- spacing system;
- radius system;
- border principles;
- shadow principles;
- icon library;
- basic component principles.

The following elements remain intentionally open and will be refined during mockup creation and frontend development:

- final semantic color values;
- final Primary color scale validation;
- exact typography line heights;
- exact shadows;
- complete component states;
- responsive breakpoints;
- detailed data visualization patterns;
- final component dimensions;
- advanced interaction patterns.

The design system should evolve incrementally as these requirements become concrete.