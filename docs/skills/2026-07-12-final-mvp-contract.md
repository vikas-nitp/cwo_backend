# Final MVP contract and data workflow

`data/source/offers.csv` is the only production offer source. Run
`python scripts/build_data_bundle.py` after editing it; validation must pass
before committing generated snapshots and the frontend distribution.

The public runtime has five flags: phase-two user features, public All Offers,
coupon codes, analytics, and booking-amount comparison. Demo authentication is
not part of the MVP. Coupon codes and amount comparisons remain server-guarded.

Synthetic test data is generated separately with
`python scripts/generate_synthetic_offers.py`. Those rows are marked
`SYNTHETIC_TEST` and the production compiler rejects them.

Regenerate `contracts/openapi.json`, export the frontend bundle, then run the
backend and frontend validation suites before updating the existing PRs.
