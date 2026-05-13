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
from cxas_scrapi.core.insights import Insights


def main():
    parser = argparse.ArgumentParser(
        description="Fetch online conversations from Contact Center Insights."
    )
    parser.add_argument(
        "--project", required=True, help="GCP Project ID for Insights."
    )
    parser.add_argument(
        "--location", default="us-central1", help="Location for Insights."
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Base output directory to save conversations.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of conversations to fetch.",
    )
    args = parser.parse_args()

    print(
        f"Fetching up to {args.limit} conversations for {args.project} in {args.location}..."
    )

    try:
        client = Insights(project_id=args.project, location=args.location)
        # Using base request/pagination to list conversations
        path = f"{client.parent}/conversations"
        conversations = client._list_paginated(
            path, "conversations", params={"view": "FULL"}
        )

        if not conversations:
            print("No conversations found.")
            return

        target_dir = os.path.join(args.output_dir, "insights_conversations")
        os.makedirs(target_dir, exist_ok=True)

        count = 0
        for conv in conversations:
            if count >= args.limit:
                break
            # Conversation name is typically projects/.../conversations/ID
            conv_id = conv.get("name", "").split("/")[-1]
            if not conv_id:
                continue

            file_path = os.path.join(target_dir, f"{conv_id}.json")
            with open(file_path, "w") as f:
                json.dump(conv, f, indent=2)
            print(f"Saved conversation {conv_id} to {file_path}")
            count += 1

        print(f"Successfully fetched and saved {count} conversations.")

    except Exception as e:
        print(f"Error fetching conversations: {e}")


if __name__ == "__main__":
    main()
