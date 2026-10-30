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
