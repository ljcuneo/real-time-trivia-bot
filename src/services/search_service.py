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
            # Handle basic math questions first
            if self._is_math_question(question):
                answer = self._calculate_math(question)
                if answer:
                    return answer
            
            # Try SERP API if available
            if self.api_key:
                answer = self._serp_api_search(question)
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
        """Search using Search API."""
        try:
            search_query = self._prepare_search_query(question)
            logger.info(f"Searching with Search API: {search_query}")
            
            url = 'https://www.searchapi.io/api/v1/search'
            headers = {
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            params = {
                'q': search_query,
                'engine': 'google',
                'google_domain': 'google.com',
                'gl': 'us',
                'hl': 'en',
                'num': '3'  # Get top 3 results for better context
            }
            
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Search API error: {response.status_code}")
                return None

            data = response.json()
            search_texts = []
            
            # Extract answer from answer box if available
            if 'answer_box' in data:
                answer_box = data['answer_box']
                if isinstance(answer_box, dict):
                    for field in ['answer', 'snippet', 'title', 'result']:
                        if field in answer_box and answer_box[field]:
                            return self._clean_answer(answer_box[field])

            # Try knowledge graph next
            if 'knowledge_graph' in data:
                kg = data['knowledge_graph']
                if isinstance(kg, dict):
                    for field in ['description', 'answer', 'snippet', 'title']:
                        if field in kg and kg[field]:
                            return self._clean_answer(kg[field])

            # Finally check organic results
            if 'organic_results' in data and data['organic_results']:
                for result in data['organic_results'][:3]:
                    for field in ['snippet', 'title']:
                        if field in result and result[field]:
                            cleaned = self._clean_answer(result[field])
                            if cleaned:
                                return cleaned

            return None
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return None

    def _prepare_search_query(self, question: str) -> str:
        """Prepare the search query to improve results."""
        # Remove question marks and clean up
        question = question.strip('?').strip().lower()
        
        # Special handling for math questions
        if re.search(r'\d[\s+\-*/]\d', question):
            return f"calculator {question}"

        # For questions asking about "most", "biggest", etc.
        superlative_pattern = r'\b(?:largest|biggest|highest|most|best)\b'
        if re.search(superlative_pattern, question):
            return f"{question} facts confirmed"

        # For questions starting with common question words
        if question.startswith(('what', 'when', 'who', 'where', 'which', 'how')):
            return f"{question} facts direct answer"
        
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
            'Advertisement',
            'According to',
            'Below, we\'ve compiled',
            'Here are',
            'In this article'
        ]
        for prefix in prefixes:
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].strip()
        
        # Remove citations and URLs
        text = re.sub(r'\[\d+\]', '', text)
        text = re.sub(r'http\S+', '', text)

        # Split into sentences
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        if not sentences:
            return text.strip()

        # Score each sentence based on information density and relevance
        scored_sentences = []
        for sentence in sentences:
            score = 0
            lower_sentence = sentence.lower()
            
            # Filter out non-answers and meta-text
            if any(word in lower_sentence for word in ['click here', 'read more', 'learn more', 'find out', 'subscribe']):
                continue
            
            # Prefer sentences with specific facts
            if re.search(r'\d', sentence):  # Contains numbers
                score += 3
            if re.search(r'\b(?:19|20)\d{2}\b', sentence):  # Contains years
                score += 2
            if re.search(r'\$\s*\d+(?:\.\d+)?', sentence):  # Contains monetary values
                score += 2
            
            # Prefer sentences that directly answer questions
            if re.search(r'\b(?:is|are|was|were|has|have|had)\b', lower_sentence):
                score += 2
            
            # Prefer sentences with key information indicators
            if re.search(r'\b(?:because|therefore|thus|hence|since|due to)\b', lower_sentence):
                score += 2
            
            # Prefer sentences with proper nouns
            if re.search(r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', sentence):
                score += 1
            
            # Prefer sentences of reasonable length
            words = sentence.split()
            if 6 <= len(words) <= 20:  # Ideal length range
                score += 2
            elif len(words) < 6:  # Too short
                score -= 1
            else:  # Too long
                score -= len(words) // 20
            
            scored_sentences.append((score, sentence))
        
        # Sort by score and length (preferring higher scores and shorter sentences)
        scored_sentences.sort(key=lambda x: (-x[0], len(x[1])))
        
        # Return the highest scoring sentence
        if scored_sentences:
            return scored_sentences[0][1].strip()
        
        # Fallback to first sentence
        return sentences[0].strip()

    def _is_math_question(self, question: str) -> bool:
        """Check if the question is a basic math question."""
        # Remove 'what is' and other common prefixes and clean whitespace
        clean_q = question.lower()
        clean_q = re.sub(r'^(?:what\s+is|calculate|solve|find|tell\s+me)\s*', '', clean_q)
        clean_q = clean_q.strip('?').strip()
        
        # Convert word operators to symbols
        clean_q = clean_q.replace('plus', '+').replace('minus', '-')
        clean_q = clean_q.replace('times', '*').replace('divided by', '/')
        
        # Look for math expression patterns
        return bool(re.match(r'^\s*\d+\s*[\+\-\*/]\s*\d+\s*$', clean_q))

    def _calculate_math(self, question: str) -> Optional[str]:
        """Calculate basic math expressions."""
        try:
            # Clean and normalize the question
            clean_q = question.lower()
            clean_q = re.sub(r'^(?:what\s+is|calculate|solve|find|tell\s+me)\s*', '', clean_q)
            clean_q = clean_q.strip('?').strip()
            
            # Convert word operators to symbols
            clean_q = clean_q.replace('plus', '+').replace('minus', '-')
            clean_q = clean_q.replace('times', '*').replace('divided by', '/')
            
            # Remove all whitespace
            clean_q = re.sub(r'\s+', '', clean_q)
            
            # Match the exact math expression
            if not re.match(r'^\d+[\+\-\*/]\d+$', clean_q):
                return None
            
            # Parse numbers and operator
            match = re.match(r'^(\d+)([\+\-\*/])(\d+)$', clean_q)
            if not match:
                return None
            
            num1, op, num2 = match.groups()
            num1, num2 = int(num1), int(num2)
            
            # Perform calculation
            if op == '+':
                result = num1 + num2
            elif op == '-':
                result = num1 - num2
            elif op == '*':
                result = num1 * num2
            elif op == '/' and num2 != 0:
                result = num1 / num2
            else:
                return None
            
            # Format result (remove trailing zeros for decimals)
            if isinstance(result, float):
                return f"{result:.6f}".rstrip('0').rstrip('.')
            return str(result)
            
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