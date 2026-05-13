# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import json
import os
import subprocess


def main():
    parser = argparse.ArgumentParser(
        description="Fetch runtime errors from Cloud Logging."
    )
    parser.add_argument(
        "--project", required=True, help="GCP Project ID for Cloud Logging."
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Base output directory to save logs.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of log entries to fetch.",
    )
    args = parser.parse_args()

    print(f"Fetching up to {args.limit} error logs for project {args.project}...")

    # Querying for errors, can be customized to filter by resource type if known
    query = "severity>=ERROR"
    cmd = [
        "gcloud",
        "logging",
        "read",
        query,
        "--project",
        args.project,
        "--limit",
        str(args.limit),
        "--format",
        "json",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logs = json.loads(result.stdout)

        if not logs:
            print("No error logs found.")
            return

        target_dir = os.path.join(args.output_dir, "cloud_logs")
        os.makedirs(target_dir, exist_ok=True)

        file_path = os.path.join(target_dir, "runtime_errors.json")
        with open(file_path, "w") as f:
            json.dump(logs, f, indent=2)

        print(f"Successfully fetched and saved {len(logs)} error logs to {file_path}")

    except subprocess.CalledProcessError as e:
        print(f"Error executing gcloud command: {e.stderr}")
    except Exception as e:
        print(f"Error processing logs: {e}")


if __name__ == "__main__":
    main()
