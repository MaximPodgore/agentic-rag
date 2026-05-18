from typing import List, Dict, Any
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from agents.tools import vector_search, keyword_search, get_document_count


class QueryResult(BaseModel):
    """Result from querying documents"""
    answer: str
    sources_cited: List[str] = []


class QueryAgent:
    """Agent that handles natural language queries using hybrid search."""

    def __init__(self, model_name: str = "gpt-4o"):
        self.model = ChatOpenAI(
            model=model_name,
            temperature=0,
        )

        self.agent = create_agent(
            model=self.model,
            response_format=ToolStrategy(QueryResult),
            system_prompt=(
                "You are a helpful assistant that searches through a user's personal documents.\n\n"
                "You have access to these tools:\n"
                "- vector_search: Find documents about concepts, ideas, topics (semantic search)\n"
                "- keyword_search: Find specific words, names, exact phrases (literal search)\n"
                "- get_document_count: Check how many documents are indexed\n\n"
                "Follow this EXACT workflow:\n"
                "1. Call BOTH vector_search AND keyword_search with your initial query\n"
                "2. Review the results - if you have enough information, IMMEDIATELY call the final response with your answer and sources_cited\n"
                "3. Only search again if the first search returned no relevant results\n\n"
                "DO NOT make more than 2 rounds of searches. After reviewing results, you MUST answer.\n\n"
                "Cite the source file(s) for each piece of information in your answer."
            ),
            tools=[vector_search, keyword_search, get_document_count],
        )

    def query(self, question: str) -> Dict[str, Any]:
        """
        Process a natural language question and return an answer.
        """
        content = f"Answer this question based on the user's documents: {question}\n\n"

        chat = [
            {
                "role": "user",
                "content": content,
            }
        ]

        result = self.agent.invoke(
            {"messages": chat},
            config={"recursion_limit": 12}
        )

        # Extract structured output - the result is a dict with the agent's response
        query_result = None
        if isinstance(result, dict):
            # Check for structured_response first (where ToolStrategy puts it)
            query_result = result.get('structured_response') or result.get('output')
        elif hasattr(result, 'structured_response'):
            query_result = result.structured_response
        elif hasattr(result, 'output'):
            query_result = result.output
        else:
            query_result = result

        if isinstance(query_result, QueryResult):
            return {
                "question": question,
                "answer": query_result.answer,
                "sources": query_result.sources_cited,
            }
        elif isinstance(query_result, dict):
            # Handle case where pydantic model was serialized
            return {
                "question": question,
                "answer": query_result.get('answer', str(query_result)),
                "sources": query_result.get('sources_cited', []),
            }

        # Fallback for string output
        answer = str(query_result) if query_result else "No response generated"
        return {
            "question": question,
            "answer": answer,
            "sources": [],
        }
