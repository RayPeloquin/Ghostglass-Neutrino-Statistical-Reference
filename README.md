# Ghostglass-Neutrino-Statistical-Reference
CHRONOVISOR–N/S Ghostglass: synthetic on/off statistical reference, court review, protocol tests and concept visualization. Hardware unvalidated.

## Run the published software

With the packages listed in [requirements.txt](requirements.txt) installed, run these commands from the repository root:

```bash
python3 -m unittest -v test_protocol.py
python3 experiment.py
```

The experiment regenerates `results.json`. The committed [reference results](results.json) and [test record](test-record.txt) provide the saved baseline.

- [Experiment source](experiment.py)
- [Protocol tests](test_protocol.py)

## Historical release archive

[Download the original v0.1 review-and-tests archive](Ghostglass-v0.1-review-and-tests.zip). This historical archive contains its original 14-test suite. The current checkout includes an additional replay regression test and passes 15 protocol tests; use the checkout for the corrected replay validation. The earlier concept artwork reports 13 tests and is a historical visualization, not the current test record.

These are synthetic statistical and software checks. They do not demonstrate a working neutrino detector or validate hardware performance. The archive is retained as the historical release; its contents have not been updated with the checkout fixes.
