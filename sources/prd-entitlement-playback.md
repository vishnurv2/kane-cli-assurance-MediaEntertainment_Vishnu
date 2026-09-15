# PRD: Catalogue Entitlement and Playback Access

**Owner:** Product, Streaming Platform
**Status:** Approved for build
**Target application:** StreamRights demo catalogue (served at `APP_URL`)

## Background

A viewer opening the catalogue sees titles we have the right to show them. What
we have the right to show depends on the viewer's territory and their
subscription tier. This document defines what the product must do when a viewer
tries to browse or play a title.

The catalogue has no authentication. A viewer's territory and subscription tier
are selected directly in the page header, and every requirement below is
evaluated against those two selections. There is no sign-in step, no account,
and no credentials.

Territories in scope: IN, GB, US.
Subscription tiers in scope: Free (ad supported), Standard, Premium.

## Requirements

### R1 - Viewer can browse the catalogue for their territory

On opening the catalogue, a viewer sees the list of titles licensed for their
current territory. Titles not licensed for that territory are not shown in the
browse list.

### R2 - Viewer can open a title and see its availability

Selecting a title from the browse list opens that title's detail page. The
detail page shows the title name, its certification rating, and whether the
title is playable for this viewer.

### R3 - An entitled viewer can start playback

When a title is licensed for the viewer's territory and included in the viewer's
subscription tier, selecting Play starts the player and the player reports the
title now playing.

### R4 - A viewer outside the licensed territory is blocked

When a viewer's territory is not among the title's licensed territories, Play
does not start the player. The reason for the block is clearly indicated to the
viewer.

### R5 - A viewer below the required tier is blocked and offered an upgrade

When a title requires a higher subscription tier than the viewer holds, Play
does not start the player. The viewer is shown an upgrade path to the tier that
would grant access.

### R6 - Changing territory re-evaluates the catalogue

When a viewer's territory changes, the browse list is re-evaluated so that it
reflects the licensed titles for the new territory, without requiring a sign-in
again.
