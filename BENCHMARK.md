> These results were obtained by running [`benchmark.sh`](benchmark.sh) on a standard 2-core GitHub Codespaces VM.

| Command                                                                                         |         Mean [s] | Min [s] | Max [s] |    Relative |
|:------------------------------------------------------------------------------------------------|-----------------:|--------:|--------:|------------:|
| `aria2c -x4 -s4 --disk-cache=20M -q http://speedtest.tele2.net/100MB.zip -d . -o aria_test.zip` |   54.706 ± 6.221 |  38.750 |  59.084 | 1.01 ± 0.13 |
| `axel -n 4 -q -o axel_test.zip http://speedtest.tele2.net/100MB.zip`                            |   53.932 ± 3.662 |  46.632 |  56.334 |        1.00 |
| `curl -s -o curl_test.zip http://speedtest.tele2.net/100MB.zip`                                 | 202.358 ± 48.016 |  65.851 | 222.605 | 3.75 ± 0.93 |
| `uv run download_manager.py --url http://speedtest.tele2.net/100MB.zip --benchmark`             |   54.700 ± 7.143 |  34.413 |  57.783 | 1.01 ± 0.15 |
