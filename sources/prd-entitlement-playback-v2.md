# PRD: Catalogue Entitlement and Playback Access

**Owner:** Product, Streaming Platform
**Status:** Approved for build
**Version:** 2.0 - supersedes 1.0 of this document
**Target application:** StreamRights demo catalogue (served at `APP_URL`)

## Why this revision exists

Version 1.0 could not be built as written. R1 removed out-of-territory titles
from the browse list; R2 made the browse list the only route to a detail page;
R4 then specified a blocked-playback state on a detail page no viewer could
reach. The three requirements were individually reasonable and jointly
impossible, and the contradiction was found before the build shipped.

This revision resolves it by relaxing R1: a title the viewer is not licensed for
is now **shown and marked unavailable** rather than hidden. That is what viewers
expect from a streaming catalogue - a title they have heard of should not
silently vanish - and it makes the block reason in R4 reachable, and therefore
testable.

Relaxing R1 has a second consequence the Licensing schedule already anticipated:
once a viewer can see a title they cannot play, a title outside its licence
window becomes expressible too. R8 below covers that case.

## Background

A viewer opening the catalogue sees the titles we carry for their market. What
they may *play* depends on the viewer's territory and their subscription tier,
and on the licence window the title sits in. This document defines what the
product must do when a viewer browses or plays.

The catalogue has no authentication. A viewer's territory and subscription tier
are selected directly in the page header, and every requirement below is
evaluated against those two selections. There is no sign-in step, no account,
and no credentials.

Territories in scope: IN, GB, US.
Subscription tiers in scope: Free (ad supported), Standard, Premium.

## Requirements

### R1 - Viewer sees the catalogue for their market, availability marked

On opening the catalogue, a viewer sees every title we carry. A title licensed
for the viewer's current territory is shown as available. A title not licensed
for that territory is still listed, and is marked unavailable.

*Changed in 2.0. Version 1.0 hid unlicensed titles entirely.*

### R2 - Viewer can open a title and see its availability

Selecting a title from the browse list opens that title's detail page. The
detail page shows the title name, its certification rating, and whether the
title is playable for this viewer.

### R3 - An entitled viewer can start playback

When a title is licensed for the viewer's territory and included in the viewer's
subscription tier, selecting Play starts the player and the player reports the
title now playing.

### R4 - A viewer outside the licensed territory is blocked, with the ground named

When a viewer's territory is not among the title's licensed territories, Play
does not start the player. The viewer is told that the title is not licensed in
their region - the territory ground specifically, not a generic unavailability
message.

*Reachable as of 2.0. Under 1.0 no viewer could arrive at this state.*

### R5 - A viewer below the required tier is blocked and offered an upgrade

When a title requires a higher subscription tier than the viewer holds, Play
does not start the player. The viewer is shown an upgrade path to the tier that
would grant access.

### R6 - Changing territory re-evaluates the catalogue

When a viewer's territory changes, the browse list is re-evaluated so that the
availability marking on every title reflects the new territory, without
requiring a sign-in again.

*Changed in 2.0: the list membership no longer changes, only the marking.*

### R7 - An unavailable title states why it is unavailable

A title marked unavailable in the browse list carries the reason for that state:
not licensed in this region, or requires a higher plan. A viewer must be able to
tell the two apart without opening the title.

*New in 2.0. Follows from R1 - a marking with no explanation invites support
contacts.*

### R8 - A title outside its licence window is not playable

When the current date falls outside a title's licensed window, Play does not
start the player, regardless of territory and tier. A title whose window has not
yet opened is shown as coming soon together with the date it becomes available.
A title whose window has closed is not shown.

*New in 2.0. Expressible only because R1 now permits a visible-but-unplayable
state. Aligns this document with the windows in the Licensing schedule.*
