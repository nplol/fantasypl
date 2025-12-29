# NPLOL Fantasy Premier League - Operating Procedures

> Detailed step-by-step procedures for maintaining the league statistics and documentation

## Table of Contents

1. [Overview](#overview)
2. [Annual Workflow](#annual-workflow)
3. [Season-End Statistics Generation](#season-end-statistics-generation)
4. [Marathon Table Update](#marathon-table-update)
5. [Hall of Fame Update](#hall-of-fame-update)
6. [Cup Documentation](#cup-documentation)
7. [Data Validation](#data-validation)
8. [Troubleshooting](#troubleshooting)

---

## Overview

This document outlines the standard operating procedures for maintaining the NPLOL Fantasy Premier League statistics repository. All procedures are designed to be executed by league administrators after each FPL season concludes.

### Responsibility Matrix

| Task | Primary | Backup | Frequency |
|------|---------|--------|-----------|
| Statistics Generation | Admin | - | Annual |
| Marathon Table Update | Admin | - | Annual |
| Hall of Fame Update | Admin | - | When records broken |
| Cup Documentation | Admin | - | Annual |
| Repository Maintenance | Admin | - | As needed |

---

## Annual Workflow

### Season Timeline

```mermaid
gantt
    title Annual League Maintenance Schedule
    dateFormat  YYYY-MM-DD
    section FPL Season
    Regular Season (GW1-38)    :active, season, 2024-08-16, 2025-05-25
    section Post-Season
    Statistics Generation      :stats, after season, 7d
    Marathon Table Update      :marathon, after stats, 3d
    Hall of Fame Review        :hof, after marathon, 2d
    Cup Documentation          :cup, after hof, 2d
    Final Review & Push        :final, after cup, 1d
```

### High-Level Workflow

```mermaid
flowchart TD
    START([Season Ends]) --> A
    A[Wait 24-48h for FPL<br/>to finalize all points] --> B
    B[Generate season statistics] --> C
    C[Update marathon table] --> D
    D[Check for broken records] --> E{Records<br/>broken?}
    E -->|Yes| F[Update Hall of Fame]
    E -->|No| G[Skip Hall of Fame]
    F --> H
    G --> H[Document cup results]
    H --> I[Review all changes]
    I --> J[Commit to repository]
    J --> K[Push to GitHub]
    K --> END([Complete])

    style START fill:#27ae60,color:#fff
    style END fill:#3498db,color:#fff
```

---

## Season-End Statistics Generation

### Prerequisites

- [ ] FPL season completed (GW38 finished)
- [ ] All bonus points allocated (24-48h after final game)
- [ ] Access to fplstats tool
- [ ] League ID available

### Procedure

#### Step 1: Verify Season Completion

```bash
# Check FPL API for final standings
# Ensure all managers have GW38 scores
# Verify bonus points are allocated
```

**Verification Checklist:**
- [ ] GW38 deadline passed
- [ ] All matches completed
- [ ] Bonus points visible in FPL app
- [ ] No pending point corrections announced

#### Step 2: Run Statistics Generator

```bash
# Navigate to fplstats tool
cd /path/to/fplstats

# Run against league
python fplstats.py --league-id [LEAGUE_ID] --season [YEAR]
```

**Output:**
- Statistics file generated
- ~750 lines of ASCII-formatted tables
- 35+ statistical categories

#### Step 3: Export Statistics File

```bash
# Copy output to repository
cp output/statistics.txt /path/to/fantasypl/statistics/YYYY_YYYY.txt

# Example for 2024/25 season
cp output/statistics.txt /path/to/fantasypl/statistics/2024_2025.txt
```

**File Naming Convention:**
```
Format: YYYY_YYYY.txt
Example: 2024_2025.txt (for 2024/25 season)
```

#### Step 4: Validate Statistics

Run through validation checklist:

- [ ] File contains all 35+ categories
- [ ] All 10 managers listed in each category
- [ ] Points totals match FPL website
- [ ] Rankings are correctly ordered
- [ ] No formatting errors in ASCII tables

#### Step 5: Commit Statistics

```bash
cd /path/to/fantasypl

# Stage the new statistics file
git add statistics/YYYY_YYYY.txt

# Commit with season identifier
git commit -m "YYYY/YY"

# Example
git commit -m "2024/25"
```

### Statistics File Structure

```
┌─────────────────────────────────────────────────────────────────┐
│ ÅRETS [CATEGORY NAME]                                           │
│ [English description/subtitle]                                   │
├─────────────────────────────────────────────────────────────────┤
│ Rank │ Manager   │ Metric1    │ Metric2    │ Metric3           │
├──────┼───────────┼────────────┼────────────┼───────────────────┤
│ 1    │ Manager1  │ value      │ value      │ value             │
│ 2    │ Manager2  │ value      │ value      │ value             │
│ ...  │ ...       │ ...        │ ...        │ ...               │
│ 10   │ Manager10 │ value      │ value      │ value             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Marathon Table Update

### Prerequisites

- [ ] Season statistics generated
- [ ] Access to Google Sheets
- [ ] Final points for all managers

### Procedure

#### Step 1: Open Google Sheets

Navigate to: `https://docs.google.com/spreadsheets/d/137-UoJ2gj5-bD5h-LOOTsttm35dNv5QM7CocSbs0Zio`

#### Step 2: Add New Season Column

1. Insert new column after most recent season
2. Add header: `YYYY/YY` (e.g., `2024/25`)
3. Format column to match existing style

#### Step 3: Enter Season Data

For each manager:

```mermaid
flowchart TD
    A[Select manager row] --> B{Did manager<br/>participate?}
    B -->|Yes| C[Enter actual points from FPL]
    B -->|No| D[Calculate penalty]
    D --> E["Penalty = MIN(all points) - 20"]
    E --> F[Enter penalty value]
    C --> G[Move to next manager]
    F --> G
    G --> H{More<br/>managers?}
    H -->|Yes| A
    H -->|No| I[Proceed to calculations]
```

**Non-Participation Penalty Formula:**
```
If manager did NOT participate:
    penalty_points = MIN(points of all participating managers) - 20
    Mark with asterisk (*) in marathon.md
```

#### Step 4: Update Calculated Columns

1. **5-Year Rolling Sum:**
   - Sum of most recent 5 seasons
   - Formula: `=SUM([current year]:[current year - 4])`

2. **Total Sum:**
   - Sum of all seasons participated
   - Formula: `=SUM(all season columns)`

3. **Update Rankings:**
   - Sort by 5-year rolling sum (descending)
   - Assign ranks 1-10

#### Step 5: Export to CSV

```bash
# Export Google Sheet to CSV
# File > Download > Comma Separated Values (.csv)
# Save as marathon.csv

# Copy to repository
cp ~/Downloads/marathon.csv /path/to/fantasypl/marathon.csv
```

#### Step 6: Update marathon.md

Update the markdown file with new rankings:

```markdown
# Marathon

Ranking sortert etter 5 year rolling sum.

| Team | ... | YYYY/YY | 5 year rolling sum | sum |
| --- | --- | --- | --- | --- |
| Manager1 | ... | XXXX | XXXX | XXXX |
| Manager2* | ... | XXXX | XXXX | XXXX |
...
```

**Note:** Add asterisk (*) for managers who didn't participate in a season.

#### Step 7: Commit Changes

```bash
git add marathon.csv marathon.md
git commit -m "Update marathon.md"
```

---

## Hall of Fame Update

### Prerequisites

- [ ] Current season statistics available
- [ ] Previous records documented
- [ ] Understanding of record categories

### Record Categories

#### Hall of Fame Records

| Record | Metric | Current Holder | Current Value |
|--------|--------|----------------|---------------|
| Highest GW Rank | GW rank position | Nicolay | 13 of 11.5M |
| Most Participations | Seasons played | Severin | 16 |
| Most League Titles | 1st place finishes | Severin, Håvard, Øystein | 3 each |
| Most Cup Wins | Cup victories | Multiple | 1 each |
| Highest Season Points | Total points | Øystein | 2,601 |
| Highest Overall Rank | Season-end rank | Øystein | 2,011 |
| Best GW38 Rank | Final GW rank | Øystein | 3,449 of 10.9M |

#### Hall of Shame Records

| Record | Metric | Current Holder | Current Value |
|--------|--------|----------------|---------------|
| Traitor Award | Non-participation | Steffen | 2021/22, 2022/23 |
| Lowest GW Rank | Worst GW performance | Nicolay | 11.2M of 11.4M |
| Lowest Overall Rank | Worst season-end | Steffen | 6.1M of 11.5M |

### Procedure

#### Step 1: Review Current Season Performance

Check statistics file for potential record-breakers:

```bash
# Key sections to check:
# - ÅRETS HØYESTE RANK (Highest rank)
# - ÅRETS LAVESTE RANK (Lowest rank)
# - Final standings (total points)
# - Participation status
```

#### Step 2: Compare Against Records

```mermaid
flowchart TD
    A[Get current season value] --> B{Value > Record?}
    B -->|Yes| C[Record broken - update]
    B -->|No| D[No update needed]
    C --> E[Document new record]
    E --> F[Add season context]
    F --> G[Update hall-of-fame-and-shame.md]
```

#### Step 3: Update Documentation

Edit `hall-of-fame-and-shame.md`:

```markdown
## Hall of fame

| Attribute | Name | Value |
| --- | --- | --- |
| Highest GW-rank (FPL) | [Name] | [Rank] of [Total] (top X%) - [Season] |
...

## Hall of shame

| Attribute | Name | Value |
| --- | --- | --- |
| Traitor award | [Name] | [Season(s)] |
...
```

#### Step 4: Commit Changes

```bash
git add hall-of-fame-and-shame.md
git commit -m "Update hall-of-fame-and-shame.md"
```

---

## Cup Documentation

### Prerequisites

- [ ] Cup final completed
- [ ] Trophy photos taken
- [ ] Winner and runner-up confirmed

### Procedure

#### Step 1: Create Season Image Folder

```bash
cd /path/to/fantasypl/pics

# Create folder for new season
mkdir YYYY_YYYY

# Example
mkdir 2024_2025
```

#### Step 2: Add Trophy Photos

```bash
# Copy photos to folder
cp /path/to/photos/*.jpg YYYY_YYYY/

# Recommended naming:
# - winner.jpg (winner celebration)
# - trophy.jpg (trophy photo)
# - cup.jpg (cup ceremony)
# - balls.jpg (draw balls if applicable)
```

**Image Guidelines:**
- Format: JPG preferred
- Size: Reasonable file size (< 500KB each)
- Content: Trophy, winner, celebration moments

#### Step 3: Update cup.md

Add new season section at top of file:

```markdown
## YYYY/YY

![YYYY_YYYY](https://raw.githubusercontent.com/nplol/fantasypl/master/pics/YYYY_YYYY/winner.jpg)
![YYYY_YYYY](https://raw.githubusercontent.com/nplol/fantasypl/master/pics/YYYY_YYYY/trophy.jpg)
```

#### Step 4: Commit Changes

```bash
git add pics/YYYY_YYYY/*
git add cup.md
git commit -m "Update cup.md"
```

---

## Data Validation

### Statistics Validation Checklist

| Check | Method | Expected |
|-------|--------|----------|
| Manager count | Count unique names | 10 managers |
| Category count | Count section headers | 35+ categories |
| Points accuracy | Compare to FPL | Match exactly |
| Ranking order | Check descending | Correct order |
| Formatting | Visual inspection | Clean ASCII tables |

### Marathon Table Validation

| Check | Method | Expected |
|-------|--------|----------|
| Row count | Count manager rows | 10 rows |
| Column count | Count season columns | All seasons |
| Sum accuracy | Verify calculations | Correct totals |
| Penalty marking | Check asterisks | Non-participants marked |

### Common Validation Issues

1. **Points Mismatch:**
   - Wait additional 24h for FPL corrections
   - Re-run statistics generator

2. **Missing Manager:**
   - Verify league membership
   - Check for name variations

3. **Formatting Errors:**
   - Check for special characters
   - Verify ASCII table alignment

---

## Troubleshooting

### Common Issues

#### Issue: Statistics file incomplete

```
Symptom: Missing categories in output
Cause: API timeout or rate limiting
Solution: Wait and retry, or run in batches
```

#### Issue: Points don't match FPL

```
Symptom: Total points differ from FPL website
Cause: FPL point corrections after generation
Solution: Wait 48h after season end, regenerate
```

#### Issue: Manager missing from statistics

```
Symptom: Only 9 managers in output
Cause: Manager left/joined league mid-season
Solution: Manually add with available data
```

#### Issue: Image not displaying in cup.md

```
Symptom: Broken image link
Cause: Incorrect GitHub raw URL
Solution: Verify path:
  https://raw.githubusercontent.com/nplol/fantasypl/master/pics/YYYY_YYYY/filename.jpg
```

### Emergency Procedures

#### Manual Statistics Generation

If fplstats tool unavailable:
1. Export data from FPL website
2. Manually create ASCII tables
3. Follow existing file format exactly

#### Data Recovery

If repository corrupted:
1. Clone fresh from GitHub
2. Restore from Google Sheets backup
3. Regenerate statistics if needed

---

## Quick Reference

### Git Commands

```bash
# View status
git status

# Stage all changes
git add .

# Commit with message
git commit -m "Message"

# Push to GitHub
git push origin master

# Pull latest
git pull origin master
```

### File Locations

| File | Path |
|------|------|
| Statistics | `statistics/YYYY_YYYY.txt` |
| Marathon | `marathon.md`, `marathon.csv` |
| Hall of Fame | `hall-of-fame-and-shame.md` |
| Cup | `cup.md` |
| Images | `pics/YYYY_YYYY/` |

### Key URLs

| Resource | URL |
|----------|-----|
| Repository | github.com/nplol/fantasypl |
| Google Sheets | [Marathon Spreadsheet](https://docs.google.com/spreadsheets/d/137-UoJ2gj5-bD5h-LOOTsttm35dNv5QM7CocSbs0Zio) |
| fplstats | github.com/oyshan/fplstats |
| FPL Official | fantasy.premierleague.com |

---

*Last updated: December 2025*
