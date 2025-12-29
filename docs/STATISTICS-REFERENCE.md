# NPLOL Fantasy Premier League - Statistics Reference Guide

> Complete reference for all 35+ statistical categories tracked across seasons

## Table of Contents

1. [Overview](#overview)
2. [Performance Categories](#performance-categories)
3. [Position & Leadership Categories](#position--leadership-categories)
4. [Player Statistics Categories](#player-statistics-categories)
5. [Form & Consistency Categories](#form--consistency-categories)
6. [Squad Management Categories](#squad-management-categories)
7. [Chip & Transfer Categories](#chip--transfer-categories)
8. [Negative Categories](#negative-categories)
9. [Ranking Categories](#ranking-categories)
10. [Calculation Methods](#calculation-methods)
11. [Data Interpretation](#data-interpretation)

---

## Overview

Each season's statistics file contains approximately **35+ distinct categories**, providing comprehensive analysis of every aspect of FPL management. This reference guide explains each category, its calculation method, and how to interpret the data.

### Category Structure

```
┌─────────────────────────────────────────────────────────────────┐
│ ÅRETS [NORWEGIAN NAME]                                          │
│ [English Translation / Description]                             │
├─────────────────────────────────────────────────────────────────┤
│ Rank │ Manager    │ Primary Metric │ Secondary Metrics...      │
├──────┼────────────┼────────────────┼───────────────────────────┤
│ 1    │ TopManager │ Best Value     │ Supporting data...        │
│ ...  │ ...        │ ...            │ ...                       │
│ 10   │ LastMgr    │ Lowest Value   │ Supporting data...        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Performance Categories

### ÅRETS VISJONÆRE (Visionary of the Year)

**Purpose:** What-if analysis showing hypothetical scores if GW1 squad remained frozen

| Metric | Description |
|--------|-------------|
| GW1 Team | Squad selected for gameweek 1 |
| Hypothetical Total | Points accumulated by GW1 players through entire season |
| Actual Total | Manager's actual season points |
| Difference | Gap between hypothetical and actual |

**Calculation:**
```
For each player in GW1 starting XI:
    sum(player_points_all_gameweeks)
Add captain bonus from GW1 captain selection
```

**Interpretation:**
- Higher hypothetical = good initial squad picks
- Large positive difference = successful transfers improved squad
- Negative difference = transfers hurt overall performance

---

### ÅRETS CAPTAIN FORESIGHT (Captain Insight)

**Purpose:** Measures effectiveness of captain selection decisions

| Metric | Description |
|--------|-------------|
| Total Captain Points | All points from captain selections |
| Extra Points (C) | Bonus points from captain multiplier |
| Extra Points (VC) | Bonus points from vice-captain when activated |
| Triple Captain Points | Points from TC chip usage |

**Calculation:**
```
Regular Captain: captain_points × 2 (bonus = captain_points × 1)
Triple Captain: captain_points × 3 (bonus = captain_points × 2)
Vice Captain (activated): vc_points × 2 (when captain doesn't play)
```

**Interpretation:**
- Higher extra points = better captain picks
- Low VC activation = good captain availability

---

### ÅRETS CAPTAIN HINDSIGHT (Captain in Retrospect)

**Purpose:** Shows base squad performance excluding captaincy bonus

| Metric | Description |
|--------|-------------|
| Non-Captain Points | Total points excluding captain bonus |
| Best Non-Captain | Highest-scoring non-captain player |
| Missed Captain Points | Points left on table from suboptimal picks |

**Calculation:**
```
non_captain_points = total_points - captain_bonus_points
```

**Interpretation:**
- High non-captain points = strong overall squad
- Compare with Captain Foresight to see captaincy impact

---

### ÅRETS MVP (Most Valuable Player)

**Purpose:** Identifies each manager's highest-scoring player

| Metric | Description |
|--------|-------------|
| Player Name | Highest scorer for manager's teams |
| Total Points | Points accumulated by MVP |
| Gameweeks Owned | Number of GWs player was in squad |
| Points Per GW | Average contribution |

**Interpretation:**
- Common MVPs across managers = template picks
- Unique MVPs = successful differential strategy

---

### ÅRETS BESTE DIFF (Best Differential)

**Purpose:** Rewards successful low-ownership picks

| Metric | Description |
|--------|-------------|
| Differential Points | Ownership-weighted point value |
| Total Points | Raw points from differentials |
| Average Ownership | Mean ownership of differential picks |
| Best Pick | Single highest differential return |

**Calculation:**
```
For players with ownership < 30%:
    diff_points = gw_points / ownership_percentage
    total_diff = sum(diff_points)
```

**Interpretation:**
- High differential points = successful contrarian picks
- Shows template-breaking strategy success

---

## Position & Leadership Categories

### ÅRETS LENGSTE LEDER (Longest Leader)

**Purpose:** Tracks gameweeks spent in first place

| Metric | Description |
|--------|-------------|
| Weeks in 1st | Total gameweeks leading the league |
| First Lead GW | When leadership was first achieved |
| Final Position | Season-end ranking |

**Interpretation:**
- Leader ≠ winner (can lose lead late)
- Shows season-long dominance

---

### ÅRETS LENGSTE BALLETAK (Longest Bottom)

**Purpose:** Tracks gameweeks spent in last place

| Metric | Description |
|--------|-------------|
| Weeks in Last | Total gameweeks in 10th position |
| First Bottom GW | When last place was first occupied |
| Final Position | Season-end ranking |

**Interpretation:**
- Resurrection stories (bottom to high finish)
- Consistent struggles vs temporary dips

---

### ÅRETS STØRSTE LEDER (Biggest Leader)

**Purpose:** Measures maximum point advantage while leading

| Metric | Description |
|--------|-------------|
| Max Gap | Largest lead over 2nd place |
| Gap GW | Gameweek when max gap achieved |
| Final Gap | Season-end margin |

**Interpretation:**
- Large gaps early may shrink
- Shows peak dominance moments

---

### ÅRETS STØRSTE BALLETAK (Biggest Deficit)

**Purpose:** Measures maximum point deficit while last

| Metric | Description |
|--------|-------------|
| Max Deficit | Largest gap to 9th place |
| Deficit GW | Gameweek when max deficit occurred |
| Recovery | Points gained from low point |

**Interpretation:**
- Large comebacks are notable
- Shows resilience or lack thereof

---

### ÅRETS VINGLEPETTER (Position Swinger)

**Purpose:** Counts unique league positions held

| Metric | Description |
|--------|-------------|
| Positions Held | Number of different ranks (1-10) |
| Best Position | Highest rank achieved |
| Worst Position | Lowest rank achieved |
| Final Position | Season-end ranking |

**Interpretation:**
- High swings = volatile season
- Low swings = consistent performance (good or bad)

---

## Player Statistics Categories

### ÅRETS GULLSTØVEL (Golden Boot)

**Purpose:** Tracks goals scored by squad players

| Metric | Description |
|--------|-------------|
| Total Goals | All goals by owned players |
| Top Scorer | Player with most goals |
| Goals Owned | Goals while in manager's squad |

**Calculation:**
```
For each gameweek:
    sum(goals scored by players in starting XI)
    sum(goals scored by bench players if subbed in)
```

---

### ÅRETS ASSISTKONGE (Assist King)

**Purpose:** Tracks assists by squad players

| Metric | Description |
|--------|-------------|
| Total Assists | All assists by owned players |
| Top Assister | Player with most assists |
| Assist Points | Points from assists (3 per assist) |

---

### ÅRETS MÅLRETTEDE (Goals + Assists Combined)

**Purpose:** Combined attacking returns

| Metric | Description |
|--------|-------------|
| G+A Total | Goals plus assists combined |
| Attack Points | Points from goals and assists |
| Per GW Average | Average attacking returns |

---

### ÅRETS FORSVARSLØSE (Defenseless)

**Purpose:** Tracks goals conceded by defenders/goalkeepers

| Metric | Description |
|--------|-------------|
| Goals Against | Goals conceded by DEF/GK |
| Lost CS Points | Clean sheet points missed |
| Worst GW | Most goals conceded single GW |

**Interpretation:**
- Fewer goals against = better defensive picks
- Correlates with clean sheet success

---

### ÅRETS SKUDDSIKRE (Clean Sheet King)

**Purpose:** Tracks clean sheets earned

| Metric | Description |
|--------|-------------|
| Clean Sheets | Total CS by DEF/GK |
| CS Points | Points from clean sheets |
| Best DEF/GK | Player with most CS |

**FPL Clean Sheet Points:**
- Goalkeeper: 4 points
- Defender: 4 points
- Midfielder: 1 point

---

### ÅRETS KEEPER (Goalkeeper Award)

**Purpose:** Goalkeeper-specific performance

| Metric | Description |
|--------|-------------|
| Saves | Total saves made |
| Save Points | Points from saves (1 per 3 saves) |
| Penalty Saves | Penalties stopped |
| GK Total | Combined GK points |

---

## Form & Consistency Categories

### ÅRETS FORMSPILLER (Form Player)

**Purpose:** Best 5-gameweek consecutive window

| Metric | Description |
|--------|-------------|
| Best 5GW Total | Highest 5-consecutive GW points |
| Window | GW range (e.g., GW10-14) |
| Average Per GW | Points per gameweek in window |

**Calculation:**
```
For each 5-GW window (GW1-5, GW2-6, ..., GW34-38):
    window_total = sum(points in window)
Best = max(all window_totals)
```

---

### ÅRETS UTE-AV-FORMSPILLER (Out of Form)

**Purpose:** Worst 5-gameweek consecutive window

| Metric | Description |
|--------|-------------|
| Worst 5GW Total | Lowest 5-consecutive GW points |
| Window | GW range of bad form |
| Average Per GW | Points per gameweek in window |

---

### ÅRETS STABILE (Most Stable)

**Purpose:** Measures consistency across gameweeks

| Metric | Description |
|--------|-------------|
| Range | Difference between best and worst GW |
| Std Deviation | Statistical variance |
| Best GW | Highest single GW score |
| Worst GW | Lowest single GW score |

**Calculation:**
```
range = max(gw_points) - min(gw_points)
Smaller range = more stable
```

---

### ÅRETS HIGHSCORE (High Score)

**Purpose:** Best single gameweek performance

| Metric | Description |
|--------|-------------|
| Points | Highest GW score |
| Gameweek | When achieved |
| Captain | Who was captained |
| Chip Used | Any chip activated |

---

### ÅRETS LOWSCORE (Low Score)

**Purpose:** Worst single gameweek performance

| Metric | Description |
|--------|-------------|
| Points | Lowest GW score |
| Gameweek | When occurred |
| Captain | Who was captained |
| Issues | Red cards, injuries, etc. |

---

## Squad Management Categories

### ÅRETS BENKESLITER (Bench Warmer)

**Purpose:** Points accumulated by unused substitutes

| Metric | Description |
|--------|-------------|
| Bench Points | Total points by bench players |
| Avg Per GW | Average bench points |
| Best Bench GW | Highest single bench score |
| Wasted Points | Points that didn't count |

**Interpretation:**
- High bench points = poor squad rotation
- Indicates transfer/selection inefficiency

---

### ÅRETS SUPERINNBYTTER (Super Sub)

**Purpose:** Points gained from automatic substitutions

| Metric | Description |
|--------|-------------|
| Auto-Sub Points | Points from activated subs |
| Auto-Subs Made | Number of substitutions |
| Best Sub | Highest single auto-sub return |

**FPL Auto-Sub Rules:**
1. Player didn't play (0 minutes) in starting XI
2. Bench player did play
3. Formation remains valid

---

### ÅRETS RUNDBRENNER (Rotation Master)

**Purpose:** Number of unique players used across season

| Metric | Description |
|--------|-------------|
| Unique Players | Different players owned |
| Active Transfers | Transfers made |
| Hit Points | Points spent on transfers |
| Turnover Rate | New players per GW |

**Interpretation:**
- High unique players = aggressive transfer strategy
- Low = set-and-forget approach

---

### ÅRETS TEMPLATE (Template Manager)

**Purpose:** How closely squad matches popular picks

| Metric | Description |
|--------|-------------|
| Avg Ownership | Average ownership % of squad |
| Template Score | Similarity to most-owned players |
| Unique Picks | Players owned by <10% |

**Calculation:**
```
For each GW:
    avg_ownership = mean(ownership_% of all 15 squad players)
Season avg = mean(all GW averages)
```

**Interpretation:**
- High template = safe, consensus picks
- Low template = differential strategy

---

## Chip & Transfer Categories

### ÅRETS CHIPP-KONGE (Chip King)

**Purpose:** Points gained from chip usage

| Metric | Description |
|--------|-------------|
| Total Chip Points | Combined chip returns |
| Bench Boost | Points from BB chip |
| Triple Captain | Extra points from TC |
| Free Hit | Points from FH GW |

**Chips Available (per season):**
- 2× Wildcard (unlimited transfers, 2 windows)
- 1× Bench Boost (all 15 players score)
- 1× Triple Captain (3× captain points)
- 1× Free Hit (temporary unlimited transfers)

---

### ÅRETS PIMP (Transfer Master)

**Purpose:** Effectiveness of transfer decisions

| Metric | Description |
|--------|-------------|
| Transfer Net | Points gained - hits taken |
| Successful Transfers | Transfers with positive return |
| Hit Points | Points spent on extra transfers |
| Best Transfer | Single highest return |

**Calculation:**
```
transfer_value = points_from_player_in - points_from_player_out - hit_cost
```

---

### ÅRETS SPÅMANN (Prophet Award)

**Purpose:** Same-gameweek transfer success

| Metric | Description |
|--------|-------------|
| Same-GW Points | Points from last-minute transfers |
| Transfers Count | Number of deadline transfers |
| Success Rate | % that scored well |

**Definition:** Points from players transferred IN during the same gameweek they score.

---

### ÅRETS KARMA (Karma Award)

**Purpose:** Points missed from transferred-out players

| Metric | Description |
|--------|-------------|
| Missed Points | Points by recently sold players |
| Painful Transfers | Transfers with immediate punishment |
| Worst Decision | Single biggest miss |

**Definition:** Points scored by players in the gameweek immediately AFTER being transferred out.

---

## Negative Categories

### ÅRETS STYGGE SPILLER (Dirty Player)

**Purpose:** Points lost to cards

| Metric | Description |
|--------|-------------|
| Yellow Cards | Count and points lost (-1 each) |
| Red Cards | Count and points lost (-3 each) |
| Total Lost | Combined negative points |

---

### ÅRETS SELVEIDE (Own Goal Award)

**Purpose:** Own goals scored by squad

| Metric | Description |
|--------|-------------|
| Own Goals | Count of OGs |
| Points Lost | -2 points per own goal |
| Unluckiest Player | Player with most OGs |

---

### ÅRETS BOMSPILLER (Penalty Miss Award)

**Purpose:** Missed penalties by squad

| Metric | Description |
|--------|-------------|
| Penalties Missed | Count of misses |
| Points Lost | -2 points per miss |
| Unluckiest Taker | Player with most misses |

---

## Ranking Categories

### ÅRETS HØYESTE RANK (Highest Rank)

**Purpose:** Best global ranking achieved

| Metric | Description |
|--------|-------------|
| Best GW Rank | Highest gameweek position |
| Best Overall | Highest season rank |
| Peak GW | When best rank achieved |
| Percentile | Top X% of all players |

**Calculation:**
```
percentile = (rank / total_players) × 100
```

---

### ÅRETS LAVESTE RANK (Lowest Rank)

**Purpose:** Worst global ranking

| Metric | Description |
|--------|-------------|
| Worst GW Rank | Lowest gameweek position |
| Worst Overall | Lowest season rank |
| Trough GW | When worst rank occurred |
| Bottom Percentile | Bottom X% of players |

---

### ÅRETS BONUSSPILLER (Bonus King)

**Purpose:** Bonus points accumulated

| Metric | Description |
|--------|-------------|
| Total Bonus | All bonus points |
| 3-Bonus Count | Times player got 3 BPS |
| Best Player | Highest bonus earner |

**FPL Bonus Points System:**
- 3 points: Best BPS in match
- 2 points: Second best BPS
- 1 point: Third best BPS

---

### ÅRETS VANILLA (Vanilla Ice)

**Purpose:** Raw points without enhancements

| Metric | Description |
|--------|-------------|
| Base Points | Points without chips/captain |
| No Captain Bonus | Excluding captain multiplier |
| No Chip Boost | Excluding chip benefits |

**Calculation:**
```
vanilla_points = total_points - captain_bonus - chip_bonus - autosub_points
```

**Interpretation:**
- Shows true squad-building ability
- Removes luck/timing factors

---

## Calculation Methods

### Standard Point Calculations

```
Player Points =
    + Minutes (2 for 60+, 1 for 1-59)
    + Goals (GK/DEF: 6, MID: 5, FWD: 4)
    + Assists (3)
    + Clean Sheet (GK/DEF: 4, MID: 1)
    + Saves (1 per 3)
    + Penalty Save (5)
    + Bonus (1-3)
    - Yellow Card (-1)
    - Red Card (-3)
    - Own Goal (-2)
    - Penalty Miss (-2)
    - Goals Conceded (-1 per 2 for GK/DEF)
```

### Rolling Averages

```python
def rolling_average(points, window=5):
    return [sum(points[i:i+window])/window
            for i in range(len(points)-window+1)]
```

### Differential Points

```python
def differential_points(player_points, ownership_pct):
    if ownership_pct < 0.30:  # Under 30% owned
        return player_points / ownership_pct
    return 0
```

---

## Data Interpretation

### Reading Statistics Tables

1. **Rank Column:** Position 1-10 in category
2. **Primary Metric:** Main sorting criterion
3. **Secondary Metrics:** Supporting context
4. **Parentheticals:** Additional details

### Comparing Across Seasons

- Absolute values may vary (FPL scoring changes)
- Relative rankings within season are comparable
- 5-year trends show improvement/decline

### Key Insights to Look For

1. **Consistency:** Low range/std deviation
2. **Risk-Taking:** High differential scores
3. **Timing:** Good chip/captain decisions
4. **Squad Building:** High vanilla points
5. **Luck Factor:** Compare actual vs expected

---

## Appendix: Norwegian-English Glossary

| Norwegian | English |
|-----------|---------|
| Årets | Of the Year |
| Visjonære | Visionary |
| Lengste | Longest |
| Største | Biggest |
| Leder | Leader |
| Balletak | Bottom (colloquial) |
| Gullstøvel | Golden Boot |
| Assistkonge | Assist King |
| Formspiller | Form Player |
| Stabile | Stable |
| Benkesliter | Bench Warmer |
| Superinnbytter | Super Substitute |
| Stygge | Dirty/Ugly |
| Bomspiller | Miss Player |
| Høyeste | Highest |
| Laveste | Lowest |
| Vinglepetter | Wobbler/Swinger |
| Spåmann | Prophet/Soothsayer |
| Rundbrenner | Burnout/Rotation |

---

*Reference Guide Version 1.0 - December 2025*
