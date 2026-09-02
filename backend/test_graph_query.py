"""
Tes manual query ke knowledge graph Cognee.

Cara pakai:
    python test_graph_query.py "biaya transfer ke bank lain berapa?"
"""

import sys

from app.memory.graph_query import ask_graph

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Cara pakai: python test_graph_query.py "pertanyaan kamu"')
        sys.exit(0)

    question = sys.argv[1]
    print(f"Pertanyaan: {question}\n")

    try:
        answer = ask_graph(question)
        print(f"Jawaban: {answer}")
    except Exception as e:
        print(f"Error: {e}")