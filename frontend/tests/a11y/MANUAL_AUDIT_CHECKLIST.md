# Accessibility Manual Audit Checklist
<!-- TASK-060 / VER-022 companion document -->
<!-- One entry per screen. Sign off each item when manual review is complete. -->
<!-- This file is version-controlled; review sign-offs are tracked here. -->

## Purpose

Automated axe-core scans catch ~57 % of WCAG 2.1 AA issues (Deque research estimate).
This checklist covers the gap: keyboard navigation, screen-reader UX, focus management,
motion, and cognitive accessibility that cannot be automatically detected.

**Definition of Done for TASK-060 / VER-022:**
All automated scans pass (`npx playwright test --project=a11y-chromium`) AND all
manual items below are signed off.

---

## How to sign off

1. Test each item manually (see instructions).
2. Replace `[ ]` with `[x]` and add your initials + date: `[x] — ABC 2024-01-15`.
3. Commit the updated file to signal completion.

---

## Keyboard Navigation

| Screen | Tab order logical | All interactive elements reachable | Focus visible at all times | Modals trap / restore focus | Signed off |
|---|---|---|---|---|---|
| Home | [ ] | [ ] | [ ] | N/A | |
| Login | [ ] | [ ] | [ ] | N/A | |
| Register | [ ] | [ ] | [ ] | N/A | |
| Forgot password | [ ] | [ ] | [ ] | N/A | |
| Dashboard | [ ] | [ ] | [ ] | [ ] | |
| Profile | [ ] | [ ] | [ ] | [ ] | |
| Settings | [ ] | [ ] | [ ] | [ ] | |
| Feature list | [ ] | [ ] | [ ] | N/A | |
| Feature detail | [ ] | [ ] | [ ] | [ ] | |
| Notifications | [ ] | [ ] | [ ] | N/A | |
| Reports | [ ] | [ ] | [ ] | N/A | |

---

## Screen Reader (NVDA / VoiceOver)

Test with at least one of: NVDA + Chrome (Windows), VoiceOver + Safari (macOS/iOS).

| Screen | Headings hierarchy correct (h1→h2→h3) | Landmark regions present (nav, main, footer) | Images have meaningful alt or role="presentation" | Form labels announced correctly | Error messages announced live | Signed off |
|---|---|---|---|---|---|---|
| Home | [ ] | [ ] | [ ] | N/A | N/A | |
| Login | [ ] | [ ] | N/A | [ ] | [ ] | |
| Register | [ ] | [ ] | N/A | [ ] | [ ] | |
| Forgot password | [ ] | [ ] | N/A | [ ] | [ ] | |
| Dashboard | [ ] | [ ] | [ ] | N/A | N/A | |
| Profile | [ ] | [ ] | [ ] | [ ] | [ ] | |
| Settings | [ ] | [ ] | N/A | [ ] | [ ] | |
| Feature list | [ ] | [ ] | [ ] | N/A | N/A | |
| Feature detail | [ ] | [ ] | [ ] | N/A | N/A | |
| Notifications | [ ] | [ ] | N/A | N/A | [ ] | |
| Reports | [ ] | [ ] | [ ] | N/A | N/A | |

---

## Motion & Reduced Motion

| Item | Check | Signed off |
|---|---|---|
| All animations respect `prefers-reduced-motion: reduce` | [ ] | |
| No content flashes more than 3 times per second (WCAG 2.3.1) | [ ] | |

---

## Colour & Contrast

Automated axe checks cover most of this; items below require human judgment.

| Item | Check | Signed off |
|---|---|---|
| Focus ring visible on non-white backgrounds | [ ] | |
| Error state communicated by more than colour alone | [ ] | |
| Success / warning states communicated by more than colour alone | [ ] | |

---

## Responsive / Touch Accessibility

| Item | Check | Signed off |
|---|---|---|
| Touch target size ≥ 44×44 px on mobile viewport (WCAG 2.5.5) | [ ] | |
| Pinch-to-zoom not disabled (`user-scalable=no` absent) | [ ] | |
| Content reflows at 320 px width without horizontal scroll (WCAG 1.4.10) | [ ] | |

---

## Sign-off Summary

| Reviewer | Role | Date | Scope |
|---|---|---|---|
| | | | All screens |

> **VER-022 gate:** this checklist must be fully signed off before the accessibility
> acceptance criterion is considered met.
