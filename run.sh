#!/usr/bin/zsh

SERVER="server.py"
DOWNLOADER="download_manager.py"
VALIDATOR="verify_download.py"

clean_files() {
  echo "Deleting logs, downloads and jsons..."
  rm -f *.log
  rm -f downloaded_file*
  echo "Done."
}

run() {
  echo "Starting server..."
  python3 "$SERVER" & SERVER_PID=$!
  echo "Server started with PID $SERVER_PID"

  trap "kill $SERVER_PID 2>/dev/null" EXIT

  sleep 1

  echo "Starting downloader..."
  python3 "$DOWNLOADER"

  echo "Starting validator..."
  python3 "$VALIDATOR"

  echo "Done."
}

if [[ "$1" == "--clean" ]]; then
  clean_files
elif [[ "$1" == "--run" ]]; then
  run
else
  echo "Usage: $0 {--clean | --run}"
fi