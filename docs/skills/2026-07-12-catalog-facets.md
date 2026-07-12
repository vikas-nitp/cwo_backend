# Catalogue facets

**Date:** 2026-07-12

## Purpose and previous behavior

Replace singular catalogue filters and absent relationship data with generated mappings and self-excluding dynamic counts.

## Architecture and files changed

Every build generates `facets.snapshot.json`. `/offers` accepts repeated values, applies OR within groups and AND across groups, strictly filters banks, paginates last, and returns platform/bank/payment/channel options with counts, selection, and disabled state.

## Configuration and tests

Facet results are date-sensitive through `active_on`. Tests cover relationships, combined filters, strict bank behavior, self-exclusion, zero counts, and expired dates.

## Deployment notes, limitations, and migration

Generated base relationships are diagnostic; request facets are computed in memory over the small immutable catalogue. If the catalogue grows materially, preserve semantics while adding indexes or repository-native aggregation.
