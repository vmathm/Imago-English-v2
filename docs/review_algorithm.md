# Review Algorithm Documentation

This document explains the logic behind the flashcard review algorithm implemented in `/flashcard/review_flashcard`.

The function is a **customized variant of the SuperMemo 2 (SM-2)** algorithm, tailored for the Imago English app with educational enhancements such as gamification, role-based point scoring, and review scheduling simplification.

---

## Core Concepts

### Response Quality (1–5 scale)

- **1:** Total failure / blank memory
- **2:** Guessed / Not confident / Repeating the card because of error
- **3:** Perfect recall

Each score affects the review behavior differently.

---

## Algorithm Logic by Score

### Response Quality = 1

- Sets `ease = 1.3`, `interval = 1`
- Schedules `next_review = now + 3 seconds`
- **Real-time retry logic**: flashcard is pushed to the end of the list for new revision in this session

### Response Quality = 2

- Resets `ease = 1.3`, `interval = 1`
- Schedules `next_review = tomorrow at midnight`
- Rewards **points** based on user role (student/teacher/@dmin!)
- **Day-specific scheduling**: clean, daily-based review flow

### Response Quality = 3

- Updates `ease` with modified SM-2 formula:

```python
new_ease = ((old_ease + 0.5 - (5 - q) * (0.08 + (5 - q) * 0.02)) / 2)
```

- Clamped: `1.3 ≤ ease ≤ 2.5`
- Calculates `interval = ceil(old_interval × ease)`
- Clamped: `1 ≤ interval ≤ 365`
- Schedules `next_review = last_review + interval` (rounded to midnight)
- Rewards **interval-based points**: `points += max(1, interval / 2)`
- Increments `rate_three_count` if quality = 3 (analytics feature)



## 🔄 Differences from SuperMemo 2

| Feature                   | SM-2 Behavior                        | Imago Variant                                |
| ------------------------- | ------------------------------------ | -------------------------------------------- |
| Ease Factor Formula       | `EF' = EF - 0.8 + 0.28*q - 0.02*q^2` | Custom: flatter increase, halved and clamped |
| Retry on Failure          | Immediate (user-driven)              | Auto: card is pushed to end of session       |
| Scheduling Time           | Exact timedelta                      | Rounded to **midnight**                      |
| Points                    | Not applicable                       | Role-based gamification                  |
| `rate_three_count`        | Not applicable                       | Tracks uncertain reviews (q=3)           |
| Interval Reset on Failure | Partial reset                        | Full reset to 1 day and base ease            |

---

## Design Rationale

These changes make the review logic more suitable for a language-learning environment:

- **Midnight scheduling** = consistent daily study routines
- **Real-time retry** = better for short-term memory formation
- **Points system** = keeps learners and teachers engaged
- **Simplified ease logic** = less volatility in early repetitions

---


