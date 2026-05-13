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
import concurrent.futures
import glob
import json
import os
from google import genai
from google.genai import types


def load_cloud_logs(output_dir):
    """Loads runtime errors from cloud_logs directory."""
    logs_path = os.path.join(
        output_dir, "cloud_logs", "runtime_errors.json"
    )
    if not os.path.exists(logs_path):
        return []
    try:
        with open(logs_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading cloud logs: {e}")
        return []


def process_conversation(
    file_path, target_dir, client, cloud_logs, args
):
    print(f"Processing {file_path}...")
    try:
        with open(file_path, "r") as f:
            conv_data = json.load(f)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return

    # Extract transcript segments for context
    segments = (
        conv_data.get("transcript", {}).get("transcriptSegments", [])
    )
    formatted_transcript = []
    for seg in segments:
        role = (
            seg.get("segmentParticipant", {}).get("role", "UNKNOWN")
        )
        text = seg.get("text", "")
        formatted_transcript.append(f"{role}: {text}")

    transcript_text = "\n".join(formatted_transcript)

    # Correlate logs (simple placeholder: pass all logs or filter by time if available)
    # For robustness, we just pass a summary of errors if they exist
    errors_context = ""
    if cloud_logs:
        errors_context = json.dumps(cloud_logs[:10], indent=2)  # pass top 10 to avoid context overflow

    prompt = f"""
You are an expert AI developer tasked with converting online conversations from Contact Center Insights into test cases for the `SimulationEvals` framework.

**Target Format:**
The target format is a JSON object with `steps` and `expectations`.
Example:
{{
  "steps": [
    {{
      "static_utterance": "I need help with my account"
    }},
    {{
      "goal": "Authentication",
      "success_criteria": "The agent verifies user identity.",
      "response_guide": "Provide verification details.",
      "max_turns": 5
    }}
  ],
  "expectations": [
    "Agent should greet the user.",
    "Agent should successfully handle verification without crashing."
  ]
}}

**Instructions:**
1.  **Analyze the Conversation Transcript**: Read the provided Contact Center Insights transcript segments.
2.  **Identify User Goals**: Extract the main goals the user was trying to achieve.
3.  **Group Turns into Steps**: Group the interaction into semantic `goal` steps for Dynamic Simulation. Use `static_utterance` only for the initiation turn.
4.  **Incorporate Cloud Logging Errors**: If runtime errors are provided in the context, analyze if they correspond to unexpected agent behavior or crashes during this type of interaction. If so, add robust expectations to ensure the agent handles these scenarios gracefully in future evaluations (e.g., "Agent should not encounter a runtime exception when handling complex queries").
5.  **Global Expectations**: Put all expectations into the single `expectations` array at the root level.

**Contact Center Insights Transcript:**
{transcript_text}

**Runtime Errors Context (Cloud Logging):**
{errors_context}

Output ONLY the converted JSON object. Do not include any markdown formatting or other text outside the JSON.
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        result_json = json.loads(response.text)
        filename = os.path.basename(file_path)
        target_file = os.path.join(target_dir, filename)
        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        with open(target_file, "w") as f:
            json.dump(result_json, f, indent=2)
        print(f"Saved converted test case to {target_file}")

    except Exception as e:
        print(f"Error converting {file_path}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert Insights conversations to SimulationEvals."
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Base output directory containing insights_conversations/.",
    )
    parser.add_argument(
        "--project", default="ces-deployment-dev", help="GCP Project for Gemini."
    )
    parser.add_argument(
        "--location", default="us-central1", help="GCP Location for Gemini."
    )
    parser.add_argument(
        "--parallelism",
        type=int,
        default=5,
        help="Number of parallel conversion workers.",
    )
    args = parser.parse_args()

    source_dir = os.path.join(args.output_dir, "insights_conversations")
    target_dir = os.path.join(args.output_dir, "sim_evals_generated")

    if not os.path.exists(source_dir):
        print(f"Source directory {source_dir} does not exist.")
        return

    client = genai.Client(
        vertexai=True, project=args.project, location=args.location
    )
    cloud_logs = load_cloud_logs(args.output_dir)

    files = glob.glob(os.path.join(source_dir, "*.json"))
    print(f"Found {len(files)} conversations to convert.")

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=args.parallelism
    ) as executor:
        futures = [
            executor.submit(
                process_conversation, f, target_dir, client, cloud_logs, args
            )
            for f in files
        ]
        for future in futures:
            future.result()


if __name__ == "__main__":
    main()
