import requests
import json
import io
import re
from datetime import datetime
from pypdf import PdfReader

# Configuration (In a real app, these would be in .env)
PATRIOT_AI_API_URL = "https://patriotai.gmu.edu/api/internal/userConversations/byGptSystemId/2e6987f9-be64-4fbc-83e5-53c147935e4b"
# Using the Bearer token provided by the user (truncated for brevity in logs, but full in code)
# TODO: In production, this token should be refreshed or obtained via OAuth
PATRIOT_AI_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1cG4iOiIyNmVkMjJiYi00NTc0LTQwMDItYmI5OS03M2M2Mzc0NDMzZTUiLCJpcCI6IkVudHJhSWQiLCJlbWFpbCI6ImpkZXJvbWFAZ211LmVkdSIsInV2byI6eyJpZCI6IjI2ZWQyMmJiLTQ1NzQtNDAwMi1iYjk5LTczYzYzNzQ0MzNlNSIsIm4iOiJKb3NlcGggSGVucnkgRGVSb21hIn0sInVyIjpbXSwiY2FwIjpbXSwidiI6IjIuMjYwMy40MzE5LjAiLCJuYmYiOjE3NzExODc3ODYsImV4cCI6MTc3MTE4OTU4NiwiaWF0IjoxNzcxMTg3Nzg2fQ.lgCFLFWU4plqghHW0oF_EBPmm19gX5HssHuTj7wZlCk"
SESSION_ID = "6d8564ad-2ccd-4b0e-ae93-7878c87a555d" # Or generate a new one?

class PatriotAIClient:
    def __init__(self):
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': f'Bearer {PATRIOT_AI_TOKEN}',
            'content-type': 'application/json',
            'origin': 'https://patriotai.gmu.edu',
            'referer': 'https://patriotai.gmu.edu/chat/onechat',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
        }

    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extracts text from a PDF file using pypdf."""
        try:
            reader = PdfReader(io.BytesIO(file_content))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return ""

    def parse_syllabus(self, text_content: str):
        """Sends syllabus text to Patriot AI and asks for exam dates."""
        
        prompt = (
            "I am going to paste the text of a syllabus below. "
            "Please analyze it and identify all EXAM dates (Midterms, Finals, Tests). "
            "Return the output as a strictly formatted JSON list of objects. "
            "Each object should have keys: 'name' (string), 'date' (YYYY-MM-DD), 'time' (HH:MM if available, else null). "
            "Do not include any conversational filler, just the JSON. "
            f"\n\nSYLLABUS TEXT:\n{text_content[:15000]}" # Truncate to avoid context limits if huge
        )

        payload = {
            "question": prompt,
            "visionImageIds": [], # We act as if no image, just text
            "attachmentIds": [],
            "session": {"sessionIdentifier": SESSION_ID},
            "segmentTraceLogLevel": "NonPersisted",
            "answerGenerationOptions": {
                "deploymentIdentifier": "ChatGpt|gpt-5.2-chat",
                "capabilities": ["ImageCreation", "InternetSearch"]
            }
        }

        try:
            response = requests.post(PATRIOT_AI_API_URL, headers=self.headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                # The response from these chat APIs is usually a stream or a JSON with 'answer' field
                # Let's assume it's JSON for now based on 'application/json' content-type content
                # If it's a stream, we might need to handle ndjson
                # But let's look at the cURL again... it expects JSON.
                
                # Handling potential streaming response (Server-Sent Events) or direct JSON
                # If the response is streaming, we need to accumulate
                
                # Check content type
                if "stream" in response.headers.get("Content-Type", ""):
                    # Basic stream handler - this is a guess on format (data: {...})
                    full_answer = ""
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith("data:"):
                                try:
                                    token_data = json.loads(decoded_line[5:])
                                    # Assuming standard OpenAI-like delta structure or similar
                                    # Adjust based on actual PatriotAI response structure
                                    if 'choices' in token_data: # OpenAI style
                                        delta = token_data['choices'][0].get('delta', {}).get('content', '')
                                        full_answer += delta
                                    elif 'answer' in token_data: # Custom
                                        full_answer += token_data['answer']
                                except:
                                    pass
                    return self._parse_json_from_text(full_answer)
                else:
                    # Standard JSON
                    data = response.json()
                    # We need to find the text answer in this structure
                    # Usually 'answer', 'message', or 'choices'
                    answer = data.get('answer') or data.get('message') or str(data)
                    return self._parse_json_from_text(answer)
            else:
                print(f"Patriot AI Error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"Request failed: {e}")
            return []

    def chat(self, user_message: str) -> str:
        """
        Sends a general chat message to Patriot AI with ImageCreation and InternetSearch enabled.
        Returns the text response (which may include markdown image links).
        """
        payload = {
            "question": user_message,
            "visionImageIds": [],
            "attachmentIds": [],
            "session": {"sessionIdentifier": SESSION_ID},  # Reuse session for context
            "segmentTraceLogLevel": "NonPersisted",
            "answerGenerationOptions": {
                "deploymentIdentifier": "ChatGpt|gpt-5.2-chat",
                "capabilities": ["ImageCreation", "InternetSearch"]
            }
        }

        try:
            print(f"Sending message to Patriot AI: {user_message}")
            response = requests.post(PATRIOT_AI_API_URL, headers=self.headers, json=payload, timeout=90)
            
            if response.status_code == 200:
                # Handle potential streaming or direct JSON
                full_answer = ""
                content_type = response.headers.get("Content-Type", "")
                
                if "stream" in content_type:
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith("data:"):
                                try:
                                    token_data = json.loads(decoded_line[5:])
                                    if 'choices' in token_data:
                                        delta = token_data['choices'][0].get('delta', {}).get('content', '')
                                        full_answer += delta
                                    elif 'answer' in token_data:
                                        full_answer += token_data['answer']
                                except:
                                    pass
                else:
                    data = response.json()
                    full_answer = data.get('answer') or data.get('message') or str(data)

                print(f"Patriot AI Response: {full_answer[:200]}...")
                return full_answer
            else:
                error_msg = f"Patriot AI Error: {response.status_code} - {response.text}"
                print(error_msg)
                return "I couldn't reach Patriot AI at the moment. Please try again."

        except Exception as e:
            print(f"Request failed: {e}")
            return f"Error communicating with Patriot AI: {str(e)}"

    def _parse_json_from_text(self, text: str):
        """Extracts JSON list from a text response that might contain markdown."""
        try:
            # Find JSON/List pattern
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            return []
        except Exception as e:
            print(f"JSON Parsing failed: {e}")
            return []

# Singleton instance
patriot_client = PatriotAIClient()
