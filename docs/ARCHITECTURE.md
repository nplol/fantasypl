# NPLOL Fantasy Premier League - System Architecture

> Comprehensive documentation for the Norwegian FPL League (nplol) statistics and tracking system

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Data Flow](#data-flow)
4. [Repository Structure](#repository-structure)
5. [Components](#components)
6. [External Integrations](#external-integrations)
7. [Data Models](#data-models)
8. [Special Procedures](#special-procedures)
9. [Statistics Categories](#statistics-categories)
10. [Appendices](#appendices)

---

## Overview

### Project Summary

| Attribute | Value |
|-----------|-------|
| **Project Name** | fantasypl |
| **Type** | Documentation & Statistics Repository |
| **Purpose** | Track and archive FPL league performance |
| **Participants** | 10 Norwegian fantasy managers |
| **History** | 2009/10 - Present (16+ seasons) |
| **Repository** | github.com/nplol/fantasypl |

### League Participants

```
1. Øystein      6. Øyvind
2. Håvard       7. Jørgen
3. Andreas      8. Snorre
4. Nicolay      9. Severin
5. Torbjørn    10. Steffen
```

---

## System Architecture

### High-Level Architecture Diagram

```mermaid
graph TB
    subgraph External["External Systems"]
        FPL[("Fantasy Premier League<br/>Official API")]
        GS[("Google Sheets<br/>Raw Data Backup")]
    end

    subgraph Processing["Data Processing Layer"]
        FPLSTATS["fplstats Tool<br/>(github.com/oyshan/fplstats)"]
        MANUAL["Manual Data Entry"]
    end

    subgraph Repository["GitHub Repository"]
        subgraph Docs["Documentation Layer"]
            TAB["tabeller.md<br/>Season Tables"]
            TABRAW["tabeller-raw.md<br/>Raw Standings"]
            MAR["marathon.md<br/>5-Year Rolling"]
            CUP["cup.md<br/>Cup Results"]
            HOF["hall-of-fame-and-shame.md<br/>Records"]
        end

        subgraph Stats["Statistics Layer"]
            S2020["2020_2021.txt"]
            S2021["2021_2022.txt"]
            S2022["2022_2023.txt"]
            S2023["2023_2024.txt"]
            S2024["2024_2025.txt"]
        end

        subgraph Assets["Media Assets"]
            PICS["pics/<br/>Trophy Photos"]
        end

        subgraph Data["Structured Data"]
            CSV["marathon.csv"]
        end
    end

    FPL --> FPLSTATS
    FPLSTATS --> Stats
    GS <--> MAR
    GS <--> CSV
    MANUAL --> Docs
    Stats --> Docs
    PICS --> CUP

    style FPL fill:#3498db,color:#fff
    style GS fill:#27ae60,color:#fff
    style FPLSTATS fill:#e74c3c,color:#fff
    style Repository fill:#f8f9fa,stroke:#333
```

### Component Interaction Flow

```mermaid
sequenceDiagram
    participant FPL as FPL Official API
    participant Stats as fplstats Tool
    participant Repo as GitHub Repository
    participant GS as Google Sheets
    participant User as League Admin

    Note over FPL,User: Season End Processing (After GW38)

    FPL->>Stats: Fetch league data
    Stats->>Stats: Calculate 35+ metrics
    Stats->>Repo: Export statistics .txt file

    User->>Repo: Update tabeller.md
    User->>Repo: Update marathon.md
    User->>GS: Update raw data
    GS-->>Repo: Sync marathon.csv

    User->>Repo: Update hall-of-fame
    User->>Repo: Add trophy photos
    User->>Repo: Git commit & push

    Note over Repo: Repository updated for new season
```

---

## Data Flow

### Annual Data Flow Cycle

```mermaid
flowchart LR
    subgraph Season["FPL Season (Aug-May)"]
        GW1["Gameweek 1"]
        GW2["Gameweek 2"]
        GWN["..."]
        GW38["Gameweek 38"]
    end

    subgraph Collection["Data Collection"]
        API["FPL API<br/>Points, Transfers, Chips"]
        LIVE["Live Rankings<br/>GW & Overall"]
    end

    subgraph Processing["Season-End Processing"]
        CALC["Statistics Calculation<br/>35+ Categories"]
        FORMAT["ASCII Table Formatting"]
        EXPORT["Export to .txt"]
    end

    subgraph Archive["Repository Archive"]
        STATS["statistics/<br/>YYYY_YYYY.txt"]
        DOCS["Markdown<br/>Documentation"]
        MEDIA["Trophy<br/>Photos"]
    end

    GW1 --> GW2 --> GWN --> GW38
    GW38 --> API
    API --> CALC
    LIVE --> CALC
    CALC --> FORMAT --> EXPORT
    EXPORT --> STATS
    STATS --> DOCS
    DOCS --> MEDIA

    style GW38 fill:#e74c3c,color:#fff
    style CALC fill:#3498db,color:#fff
```

### Data Transformation Pipeline

```mermaid
flowchart TD
    subgraph Input["Raw Data Sources"]
        A1["Manager Points"]
        A2["Player Stats"]
        A3["Transfer History"]
        A4["Chip Usage"]
        A5["Captain Picks"]
    end

    subgraph Transform["Calculations"]
        B1["Points Aggregation"]
        B2["Ranking Computation"]
        B3["Differential Analysis"]
        B4["Form Windows"]
        B5["Special Awards"]
    end

    subgraph Output["Generated Statistics"]
        C1["35+ Statistical Categories"]
        C2["ASCII Formatted Tables"]
        C3["Markdown Summaries"]
    end

    A1 & A2 & A3 --> B1
    A4 & A5 --> B2
    A1 & A2 --> B3
    A1 --> B4
    B1 & B2 & B3 & B4 --> B5

    B5 --> C1 --> C2 --> C3
```

---

## Repository Structure

```
fantasypl/
├── .gitignore                    # Excludes .DS_Store
├── cup.md                        # Cup competition results
├── hall-of-fame-and-shame.md     # League records & achievements
├── marathon.csv                  # Structured 10-year data
├── marathon.md                   # 5-year rolling rankings
├── tabeller.md                   # Visual season tables
├── tabeller-raw.md               # Raw standings data
├── statistics/                   # Detailed season analytics
│   ├── 2020_2021.txt            # ~750 lines, 35+ categories
│   ├── 2021_2022.txt
│   ├── 2022_2023.txt
│   ├── 2023_2024.txt
│   └── 2024_2025.txt
├── pics/                         # Trophy/celebration photos
│   ├── 2022_2023/
│   │   ├── winner.jpg
│   │   ├── cup_and_balls.jpg
│   │   └── cup_and_balls2.jpg
│   └── 2023_2024/
│       ├── winner.jpg
│       ├── balls.jpg
│       └── cup.jpg
└── docs/                         # Documentation (this file)
    └── ARCHITECTURE.md
```

### File Size Distribution

```mermaid
pie title Repository File Distribution
    "Statistics Files" : 288
    "Trophy Images" : 1600
    "Markdown Docs" : 13
    "CSV Data" : 2
```

---

## Components

### Documentation Files

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `tabeller.md` | Visual season tables with screenshots | End of season |
| `tabeller-raw.md` | Raw markdown standings tables | End of season |
| `marathon.md` | 5-year rolling sum rankings | End of season |
| `marathon.csv` | Machine-readable marathon data | End of season |
| `cup.md` | Cup competition finals & photos | End of season |
| `hall-of-fame-and-shame.md` | All-time records | When records broken |

### Statistics Files Structure

Each `statistics/YYYY_YYYY.txt` file contains:

```
┌────────────────────────────────────────────────────────────┐
│ ÅRETS [CATEGORY NAME]                                      │
├────────────────────────────────────────────────────────────┤
│ Manager      │ Metric 1    │ Metric 2    │ Metric 3      │
│──────────────┼─────────────┼─────────────┼───────────────│
│ Øystein      │ 2,601       │ 2,011       │ ...           │
│ Håvard       │ 2,456       │ 15,234      │ ...           │
│ ...          │ ...         │ ...         │ ...           │
└────────────────────────────────────────────────────────────┘
```

---

## External Integrations

### Integration Architecture

```mermaid
graph LR
    subgraph External["External Services"]
        FPL["FPL Official<br/>fantasy.premierleague.com"]
        FPLSTATS["fplstats<br/>github.com/oyshan/fplstats"]
        GS["Google Sheets<br/>docs.google.com"]
        GH["GitHub<br/>github.com/nplol/fantasypl"]
    end

    subgraph DataFlow["Data Flow"]
        direction TB
        D1["League Data"]
        D2["Processed Stats"]
        D3["Raw Backup"]
        D4["Version Control"]
    end

    FPL -->|"API Fetch"| D1
    D1 -->|"Processing"| FPLSTATS
    FPLSTATS -->|"Statistics"| D2
    D2 -->|"Archive"| GH
    D2 -->|"Backup"| GS
    GS -->|"Sync"| D3
    GH -->|"Commits"| D4

    style FPL fill:#3d195b,color:#fff
    style GS fill:#0f9d58,color:#fff
    style GH fill:#24292e,color:#fff
```

### Integration Details

| System | Purpose | Access Method | Data Direction |
|--------|---------|---------------|----------------|
| FPL API | Source data | HTTP/REST | Inbound |
| fplstats | Processing | Local execution | Transform |
| Google Sheets | Backup | Shared document | Bidirectional |
| GitHub | Archive | Git push | Outbound |

### Google Sheets Integration

- **URL**: `https://docs.google.com/spreadsheets/d/137-UoJ2gj5-bD5h-LOOTsttm35dNv5QM7CocSbs0Zio`
- **Purpose**: Live data maintenance and collaborative editing
- **Sync**: Manual sync to `marathon.csv`

---

## Data Models

### Manager Data Model

```mermaid
classDiagram
    class Manager {
        +String name
        +int seasons_participated
        +List~Season~ seasons
        +int total_points_all_time
        +int five_year_rolling_sum
    }

    class Season {
        +String year_range
        +int total_points
        +int overall_rank
        +int league_position
        +List~Gameweek~ gameweeks
        +ChipUsage chips
    }

    class Gameweek {
        +int number
        +int points
        +int gw_rank
        +int overall_rank
        +Player captain
        +List~Transfer~ transfers
    }

    class ChipUsage {
        +Gameweek wildcard1
        +Gameweek wildcard2
        +Gameweek bench_boost
        +Gameweek triple_captain
        +Gameweek free_hit
    }

    class Transfer {
        +Player player_in
        +Player player_out
        +int cost
        +int points_gained
    }

    Manager "1" --> "*" Season
    Season "1" --> "38" Gameweek
    Season "1" --> "1" ChipUsage
    Gameweek "1" --> "*" Transfer
```

### Statistics Category Model

```mermaid
classDiagram
    class StatisticsFile {
        +String season
        +List~Category~ categories
        +DateTime generated_at
    }

    class Category {
        +String name_norwegian
        +String name_english
        +String description
        +List~Metric~ metrics
        +List~ManagerResult~ results
    }

    class Metric {
        +String name
        +String type
        +String unit
    }

    class ManagerResult {
        +String manager_name
        +Map~String,Value~ metric_values
        +int rank_in_category
    }

    StatisticsFile "1" --> "35+" Category
    Category "1" --> "*" Metric
    Category "1" --> "10" ManagerResult
```

---

## Special Procedures

### Procedure 1: Season-End Statistics Generation

```mermaid
flowchart TD
    A[Season Ends - GW38 Complete] --> B{All managers<br/>submitted GW38?}
    B -->|No| C[Wait for deadline]
    C --> B
    B -->|Yes| D[Run fplstats tool]
    D --> E[Generate statistics file]
    E --> F[Review & verify data]
    F --> G{Data correct?}
    G -->|No| H[Manual corrections]
    H --> F
    G -->|Yes| I[Commit to repository]
    I --> J[Update documentation files]
    J --> K[Push to GitHub]

    style A fill:#27ae60,color:#fff
    style K fill:#3498db,color:#fff
```

**Steps:**
1. Wait for GW38 to complete and all points finalized
2. Execute fplstats tool against league data
3. Export statistics to `statistics/YYYY_YYYY.txt`
4. Verify all 35+ categories generated correctly
5. Commit file with message "YYYY/YY" (e.g., "2024/25")
6. Update markdown documentation files
7. Push to master branch

### Procedure 2: Marathon Table Update

```mermaid
flowchart TD
    A[New season data available] --> B[Open Google Sheets]
    B --> C[Add new season column]
    C --> D[Enter points for each manager]
    D --> E{Manager participated?}
    E -->|Yes| F[Enter actual points]
    E -->|No| G[Apply penalty formula]
    G --> H["Lowest points - 20"]
    F --> I[Calculate 5-year rolling sum]
    H --> I
    I --> J[Update rankings]
    J --> K[Export to marathon.csv]
    K --> L[Update marathon.md]
    L --> M[Commit changes]

    style G fill:#e74c3c,color:#fff
```

**Non-Participation Penalty Formula:**
```
penalty_points = min(all_manager_points_this_season) - 20
```

### Procedure 3: Hall of Fame/Shame Update

```mermaid
flowchart TD
    A[Season statistics available] --> B[Review record categories]
    B --> C{Any records broken?}
    C -->|No| D[No update needed]
    C -->|Yes| E[Identify broken records]
    E --> F[Update hall-of-fame-and-shame.md]
    F --> G[Add context/season info]
    G --> H[Commit with descriptive message]

    style E fill:#f1c40f,color:#000
```

**Record Categories Tracked:**

| Hall of Fame | Hall of Shame |
|--------------|---------------|
| Highest GW rank | Lowest GW rank |
| Most participations | Traitor award (non-participation) |
| Most league titles | Lowest overall rank |
| Highest season points | - |
| Highest GW38 rank | - |

### Procedure 4: Cup Results Documentation

```mermaid
flowchart TD
    A[Cup final completed] --> B[Capture trophy photos]
    B --> C[Create season folder in pics/]
    C --> D[Add photos to folder]
    D --> E[Update cup.md with images]
    E --> F[Add winner/runner-up info]
    F --> G[Commit and push]

    style B fill:#9b59b6,color:#fff
```

---

## Statistics Categories

### Complete Category Reference

The statistics system tracks **35+ categories** per season. Below is the complete reference:

#### Performance Categories

| Norwegian | English | Description |
|-----------|---------|-------------|
| ÅRETS VISJONÆRE | Visionary | What-if analysis for GW1 frozen picks |
| ÅRETS CAPTAIN FORESIGHT | Captain Foresight | Extra points from captaincy |
| ÅRETS CAPTAIN HINDSIGHT | Captain Hindsight | Points excluding captain bonus |
| ÅRETS MVP | MVP | Highest-scoring player per team |
| ÅRETS BESTE DIFF | Best Differential | Low-ownership high-point picks |

#### Position Categories

| Norwegian | English | Description |
|-----------|---------|-------------|
| ÅRETS LENGSTE LEDER | Longest Leader | Most GWs in 1st place |
| ÅRETS LENGSTE BALLETAK | Longest Bottom | Most GWs in last place |
| ÅRETS STØRSTE LEDER | Biggest Leader | Largest point gap when 1st |
| ÅRETS STØRSTE BALLETAK | Biggest Deficit | Largest gap when last |
| ÅRETS VINGLEPETTER | Position Swinger | Most different positions held |

#### Player Statistics

| Norwegian | English | Description |
|-----------|---------|-------------|
| ÅRETS GULLSTØVEL | Golden Boot | Most goals |
| ÅRETS ASSISTKONGE | Assist King | Most assists |
| ÅRETS MÅLRETTEDE | Goal + Assist | Combined attacking returns |
| ÅRETS FORSVARSLØSE | Defenseless | Most goals conceded |
| ÅRETS SKUDDSIKRE | Clean Sheet King | Most clean sheets |
| ÅRETS KEEPER | Goalkeeper | Best GK performance |

#### Form Categories

| Norwegian | English | Description |
|-----------|---------|-------------|
| ÅRETS FORMSPILLER | Form Player | Best 5-GW window |
| ÅRETS UTE-AV-FORMSPILLER | Out of Form | Worst 5-GW window |
| ÅRETS STABILE | Most Stable | Smallest GW variance |
| ÅRETS HIGHSCORE | High Score | Best single GW |
| ÅRETS LOWSCORE | Low Score | Worst single GW |

#### Squad Management

| Norwegian | English | Description |
|-----------|---------|-------------|
| ÅRETS BENKESLITER | Bench Warmer | Most unused bench points |
| ÅRETS SUPERINNBYTTER | Super Sub | Most auto-sub points |
| ÅRETS RUNDBRENNER | Rotation Master | Most unique players used |
| ÅRETS TEMPLATE | Template | Highest avg ownership |

#### Chip & Transfer

| Norwegian | English | Description |
|-----------|---------|-------------|
| ÅRETS CHIPP-KONGE | Chip King | Most chip points |
| ÅRETS PIMP | Transfer Master | Best transfer timing |
| ÅRETS SPÅMANN | Prophet | Same-GW transfer in points |
| ÅRETS KARMA | Karma | Same-GW transfer out points |

#### Negative Categories

| Norwegian | English | Description |
|-----------|---------|-------------|
| ÅRETS STYGGE SPILLER | Dirty Player | Most card points lost |
| ÅRETS SELVEIDE | Own Goal | Most own goals |
| ÅRETS BOMSPILLER | Penalty Miss | Most penalties missed |

#### Ranking Categories

| Norwegian | English | Description |
|-----------|---------|-------------|
| ÅRETS HØYESTE RANK | Highest Rank | Best GW/overall rank |
| ÅRETS LAVESTE RANK | Lowest Rank | Worst GW/overall rank |
| ÅRETS BONUSSPILLER | Bonus King | Most bonus points |
| ÅRETS VANILLA | Vanilla | Raw points (no chips/captain) |

---

## Appendices

### Appendix A: Git Commit Convention

```
# Season update
YYYY/YY

# File updates
Update [filename].md

# Corrections
Fix [description]

# New content
Add [description]
```

### Appendix B: File Naming Convention

```
Statistics:  YYYY_YYYY.txt (e.g., 2024_2025.txt)
Images:      descriptive-name.jpg
Data:        descriptive-name.csv/md
```

### Appendix C: External Resources

| Resource | URL |
|----------|-----|
| FPL Official | https://fantasy.premierleague.com |
| fplstats Tool | https://github.com/oyshan/fplstats |
| Google Sheets | https://docs.google.com/spreadsheets/d/137-UoJ2gj5-bD5h-LOOTsttm35dNv5QM7CocSbs0Zio |
| Repository | https://github.com/nplol/fantasypl |

### Appendix D: Historical Timeline

```mermaid
timeline
    title NPLOL League History
    2009/10 : League Founded
    2015/16 : Marathon tracking begins
    2020/21 : Detailed statistics start
    2022/23 : Trophy photos added
    2023/24 : Øystein sets points record (2,601)
    2024/25 : Nicolay achieves GW rank #13
```

---

*Documentation generated: December 2025*
*Repository: github.com/nplol/fantasypl*
