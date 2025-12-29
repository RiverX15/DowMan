sudo apt update
sudo apt install -y hyperfine aria2 axel curl
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
hyperfine --warmup 2 --runs 10 \
  --prepare "rm -f aria_test.zip axel_test.zip curl_test.zip 100MB.zip" \
  --export-markdown BENCHMARK.md \
  "aria2c -x4 -s4 --disk-cache=20M -q http://speedtest.tele2.net/100MB.zip -d . -o aria_test.zip" \
  "axel -n 4 -q -o axel_test.zip http://speedtest.tele2.net/100MB.zip" \
  "curl -s -o curl_test.zip http://speedtest.tele2.net/100MB.zip" \
  "uv run download_manager.py --url http://speedtest.tele2.net/100MB.zip --benchmark"