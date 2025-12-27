The results here were obtained by running the `benchmark.sh` script in GitHub Codespaces on a 2-core VM.

| Command | Mean [s] | Min [s] | Max [s] | Relative |
|:---|---:|---:|---:|---:|
| `aria2c -x4 -s4 --disk-cache=20M -q http://speedtest.tele2.net/100MB.zip -d . -o aria_test.zip` | 25.722 ± 12.932 | 13.897 | 56.633 | 1.12 ± 0.61 |
| `axel -n 4 -q -o axel_test.zip http://speedtest.tele2.net/100MB.zip` | 22.937 ± 4.710 | 15.365 | 29.876 | 1.00 |
| `curl -s -o curl_test.zip http://speedtest.tele2.net/100MB.zip` | 36.705 ± 18.002 | 18.772 | 77.666 | 1.60 ± 0.85 |
| `uv run download_manager.py --url http://speedtest.tele2.net/100MB.zip --benchmark` | 26.473 ± 10.361 | 11.958 | 44.957 | 1.15 ± 0.51 |
