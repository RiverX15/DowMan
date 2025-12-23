| Command | Mean [s] | Min [s] | Max [s] | Relative |
|:---|---:|---:|---:|---:|
| `aria2c -x4 -s4 --disk-cache=5M -q http://speedtest.tele2.net/100MB.zip -d . -o aria_test.zip` | 21.764 ± 12.361 | 12.393 | 52.650 | 1.53 ± 0.95 |
| `uv run download_manager.py --url http://speedtest.tele2.net/100MB.zip --benchmark` | 14.241 ± 3.653 | 9.786 | 23.737 | 1.00 |
