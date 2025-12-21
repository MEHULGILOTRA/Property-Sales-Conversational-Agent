from typing import Dict, Any
from app.tools.base import BaseTool


class WebSearchTool(BaseTool):

    def run(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """
        input example:
        {
            "query": "schools near Silver Heights Dubai"
        }
        """

        return {
            "summary": "External information not available yet.",
            "sources": []
        }
