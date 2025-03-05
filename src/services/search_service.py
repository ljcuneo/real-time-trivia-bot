import requests
from bs4 import BeautifulSoup
from loguru import logger
from typing import Optional
import re
import time
import urllib.parse
import os
import json

class SearchService:
    def __init__(self):
        """Initialize search service."""
        self.api_key = os.getenv('SERP_API_KEY')
        if not self.api_key:
            logger.warning("SERP API key not found in environment variables. Using fallback search methods.")
        else:
            logger.info(f"SERP API key found: {self.api_key[:4]}...{self.api_key[-4:]}")
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        })

    def search_for_answer(self, question: str) -> Optional[str]:
        """Search for an answer to the given question."""
        try:
            # Try SERP API first if available
            if self.api_key:
                answer = self._serp_api_search(question)
                if answer:
                    return answer
            
            # Handle basic math questions directly
            if self._is_math_question(question):
                answer = self._calculate_math(question)
                if answer:
                    return answer
            
            # Fallback to Google
            answer = self._google_search(question)
            if answer:
                return answer
            
            # Finally try DuckDuckGo
            logger.info("Falling back to DuckDuckGo search")
            answer = self._duckduckgo_search(question)
            if answer:
                return answer
            
            logger.warning("No suitable answer found from any search method")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            return None

    def _serp_api_search(self, question: str) -> Optional[str]:
        """Search using SERP API."""
        try:
            search_query = self._prepare_search_query(question)
            logger.info(f"Searching with SERP API: {search_query}")
            
            params = {
                'api_key': self.api_key,
                'q': search_query,
                'gl': 'us',
                'hl': 'en',
                'google_domain': 'google.com',
                'output': 'json'
            }
            
            # Use the correct endpoint with increased timeout
            response = requests.get(
                'https://serpapi.com/search.json',
                params=params,
                timeout=15
            )
            
            # Log the response for debugging
            logger.debug(f"SERP API Response Status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"SERP API error: {response.status_code} - {response.text}")
                return None
            
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse SERP API response: {e}")
                logger.debug(f"Response text: {response.text[:500]}")
                return None
            
            # Log the response structure
            logger.debug(f"SERP API response keys: {list(data.keys())}")
            
            # Try to extract answer from different SERP features
            if 'answer_box' in data:
                logger.debug("Found answer box in response")
                answer_box = data['answer_box']
                if isinstance(answer_box, dict):
                    # Try different fields in order of preference
                    for field in ['answer', 'snippet', 'title', 'result']:
                        if field in answer_box and answer_box[field]:
                            answer = answer_box[field]
                            logger.info(f"Found answer in answer_box.{field}")
                            return self._clean_answer(answer)
            
            if 'knowledge_graph' in data:
                logger.debug("Found knowledge graph in response")
                kg = data['knowledge_graph']
                if isinstance(kg, dict):
                    # Try different fields in order of preference
                    for field in ['description', 'answer', 'snippet', 'title']:
                        if field in kg and kg[field]:
                            answer = kg[field]
                            logger.info(f"Found answer in knowledge_graph.{field}")
                            return self._clean_answer(answer)
            
            if 'organic_results' in data and len(data['organic_results']) > 0:
                logger.debug("Found organic results in response")
                first_result = data['organic_results'][0]
                if isinstance(first_result, dict):
                    # Try different fields in order of preference
                    for field in ['snippet', 'title', 'link_text']:
                        if field in first_result and first_result[field]:
                            answer = first_result[field]
                            logger.info(f"Found answer in organic_results[0].{field}")
                            return self._clean_answer(answer)
            
            logger.warning("No suitable answer found in SERP API response")
            return None
            
        except requests.Timeout:
            logger.error("SERP API request timed out, will try fallback methods")
            return None
        except requests.RequestException as e:
            logger.error(f"SERP API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error during SERP API search: {e}")
            return None

    def _is_math_question(self, question: str) -> bool:
        """Check if the question is a basic math question."""
        # Remove 'what is' and other common prefixes
        clean_q = question.lower().replace('what is', '').replace('calculate', '').strip()
        # Look for basic math operators
        return bool(re.search(r'\d[\s+\-*/]\d', clean_q))

    def _calculate_math(self, question: str) -> Optional[str]:
        """Calculate basic math expressions."""
        try:
            # Extract the math expression
            clean_q = question.lower().replace('what is', '').replace('calculate', '').strip()
            # Convert common words to operators
            clean_q = clean_q.replace('plus', '+').replace('minus', '-')
            clean_q = clean_q.replace('times', '*').replace('divided by', '/')
            
            # Extract numbers and operator
            match = re.search(r'(\d+)\s*([\+\-\*/])\s*(\d+)', clean_q)
            if not match:
                return None
                
            num1, op, num2 = match.groups()
            num1, num2 = float(num1), float(num2)
            
            result = None
            if op == '+':
                result = num1 + num2
            elif op == '-':
                result = num1 - num2
            elif op == '*':
                result = num1 * num2
            elif op == '/' and num2 != 0:
                result = num1 / num2
            
            if result is not None:
                # Format result to remove trailing zeros
                formatted = f"{result:.6f}".rstrip('0').rstrip('.')
                return f"The answer is {formatted}"
            
            return None
            
        except Exception as e:
            logger.error(f"Error during math calculation: {e}")
            return None

    def _google_search(self, question: str) -> Optional[str]:
        """Perform Google search."""
        try:
            # Clean up the question and create search query
            search_query = self._prepare_search_query(question)
            logger.info(f"Searching Google for: {search_query}")
            
            # Perform the search
            url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}&hl=en&gl=us"
            response = self.session.get(url, timeout=5)
            
            # Log response status and headers
            logger.debug(f"Google Response Status: {response.status_code}")
            logger.debug(f"Google Response Headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            # Parse the response
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Modern Google selectors
            selectors = [
                'div[data-tts="answers"]',
                'div[data-attrid*="description"]',
                'div[data-attrid*="answer"]',
                'span.ILfuVd',
                'div.wDYxhc',
                'div.kno-rdesc',
                'div.LGOjhe',
                'div.hgKElc',
                'div.FzvWSb',
                'div.IZ6rdc',
                'div.gsrt',
                'div.Z0LcW',
                'div.zCubwf',
                'div.XcVN5d',
                'div.PZPZlf',
                'div.iKJnec',
                'div.card-section'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if text and len(text) > 1:
                        cleaned = self._clean_answer(text)
                        if cleaned:
                            logger.info(f"Found answer in Google: {cleaned}")
                            return cleaned
            
            return None
            
        except Exception as e:
            logger.error(f"Error during Google search: {e}")
            return None

    def _duckduckgo_search(self, question: str) -> Optional[str]:
        """Perform DuckDuckGo search as fallback."""
        try:
            search_query = self._prepare_search_query(question)
            logger.info(f"Searching DuckDuckGo for: {search_query}")
            
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(search_query)}"
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # DuckDuckGo selectors
            selectors = [
                'div.result__snippet',
                'a.result__snippet',
                'div.result__body',
                'div.result__title'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if text and len(text) > 15:
                        cleaned = self._clean_answer(text)
                        if cleaned:
                            logger.info(f"Found answer in DuckDuckGo: {cleaned}")
                            return cleaned
            
            return None
            
        except Exception as e:
            logger.error(f"Error during DuckDuckGo search: {e}")
            return None

    def _prepare_search_query(self, question: str) -> str:
        """Prepare the search query to improve results."""
        # Remove question marks and clean up
        question = question.strip('?').strip().lower()
        
        # Special handling for math questions
        if re.search(r'\d[\s+\-*/]\d', question):
            return f"calculator {question}"
        
        # Special handling for capital questions
        if 'capital' in question:
            state_match = re.search(r'capital of ([a-z ]+)', question)
            if state_match:
                state = state_match.group(1).strip()
                return f"{state} capital city"
        
        # For other questions, keep it simple
        return question

    def _clean_answer(self, text: str) -> str:
        """Clean up the answer text."""
        if not text:
            return None
            
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common prefixes
        prefixes = [
            'Search Results',
            'Featured snippet from the web',
            'Web results',
            'People also ask',
            'Description',
            'Overview',
            'Quick Answer',
            'Top answer:',
            'Advertisement'
        ]
        for prefix in prefixes:
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].strip()
        
        # Remove citations [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        
        # Clean up whitespace and punctuation
        text = text.strip('., ')
        
        # If text is too short or looks like garbage, return None
        if len(text) < 2 or not re.search(r'[a-zA-Z]', text):
            return None
        
        # Limit length but try to end at a sentence boundary
        if len(text) > 500:
            text = text[:500]
            last_period = text.rfind('.')
            if last_period > 400:
                text = text[:last_period + 1]
        
        return text.strip() 