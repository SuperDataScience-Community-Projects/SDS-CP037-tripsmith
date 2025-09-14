import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class ParsingAgent:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    def parse_flight_request(self, message):
        """
        Use GPT to parse flight request and extract structured data
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a flight information parser. Extract flight search parameters from user messages.
                        
                        Return a JSON object with the following structure:
                        {
                            "origin": "city name or null if not found",
                            "destination": "city name or null if not found", 
                            "date": "YYYY-MM-DD format or null if not found",
                            "valid": true/false
                        }
                        
                        Rules:
                        - Extract city names (can be 1-2 words like "New York", "Los Angeles")
                        - Convert dates to YYYY-MM-DD format
                        - If any required field is missing, set valid to false
                        - Be flexible with date formats (MM/DD/YYYY, DD/MM/YYYY, etc.)
                        - Return only valid JSON, no other text"""
                    },
                    {
                        "role": "user",
                        "content": f"Parse this flight request: {message}"
                    }
                ],
            )
            
            # Extract JSON from response
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON
            try:
                parsed_data = json.loads(content)
                return (
                    parsed_data.get("origin"),
                    parsed_data.get("destination"), 
                    parsed_data.get("date"),
                    parsed_data.get("valid", False)
                )
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return None, None, None, False
                
        except Exception as e:
            print(f"Error in parsing agent: {e}")
            return None, None, None, False
