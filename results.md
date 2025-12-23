| Command | Mean [s] | Min [s] | Max [s] | Relative |
|:---|---:|---:|---:|---:|
| `aria2c -x16 -s16 -q http://speedtest.tele2.net/100MB.zip -d . -o aria_test.zip` | 65.847 ± 7.552 | 54.596 | 74.965 | 1.09 ± 0.28 |
| `uv run download_manager.py --url http://speedtest.tele2.net/100MB.zip --benchmark` | 60.484 ± 14.043 | 42.079 | 86.021 | 1.00 |
