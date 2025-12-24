| Command | Mean [s] | Min [s] | Max [s] | Relative |
|:---|---:|---:|---:|---:|
| `aria2c -x4 -s4 --disk-cache=20M -q http://speedtest.tele2.net/100MB.zip -d . -o aria_test.zip` | 55.364 ± 2.548 | 49.981 | 57.139 | 1.00 |
| `axel -n 4 -q -o axel_test.zip http://speedtest.tele2.net/100MB.zip` | 56.857 ± 0.580 | 55.564 | 57.807 | 1.03 ± 0.05 |
| `curl -s -o curl_test.zip http://speedtest.tele2.net/100MB.zip` | 204.923 ± 31.145 | 121.967 | 222.445 | 3.70 ± 0.59 |
| `uv run download_manager.py --url http://speedtest.tele2.net/100MB.zip --benchmark` | 56.858 ± 0.255 | 56.363 | 57.186 | 1.03 ± 0.05 |
