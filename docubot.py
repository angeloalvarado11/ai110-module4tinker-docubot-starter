"""
Core DocuBot class responsible for:
- Loading documents from the docs/ folder
- Building a simple retrieval index (Phase 1)
- Retrieving relevant snippets (Phase 1)
- Supporting retrieval only answers
- Supporting RAG answers when paired with Gemini (Phase 2)
"""

import os
import glob

class DocuBot:
    STOPWORDS = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
        "how", "i", "in", "is", "it", "of", "on", "or", "that", "the",
        "this", "to", "today", "was", "what", "when", "where", "which", "who",
        "why", "with"
    }

    def __init__(self, docs_folder="docs", llm_client=None):
        """
        docs_folder: directory containing project documentation files
        llm_client: optional Gemini client for LLM based answers
        """
        self.docs_folder = docs_folder
        self.llm_client = llm_client

        # Load documents into memory
        self.documents = self.load_documents()  # List of (filename, text)

        # Build paragraph chunks and index them for retrieval.
        self.chunks = self.build_chunks(self.documents)  # List of (filename, chunk_text)
        self.index = self.build_index(self.chunks)

    # -----------------------------------------------------------
    # Document Loading
    # -----------------------------------------------------------

    def load_documents(self):
        """
        Loads all .md and .txt files inside docs_folder.
        Returns a list of tuples: (filename, text)
        """
        docs = []
        pattern = os.path.join(self.docs_folder, "*.*")
        for path in glob.glob(pattern):
            if path.endswith(".md") or path.endswith(".txt"):
                with open(path, "r", encoding="utf8") as f:
                    text = f.read()
                filename = os.path.basename(path)
                docs.append((filename, text))
        return docs

    # -----------------------------------------------------------
    # Chunk Construction (paragraph level retrieval)
    # -----------------------------------------------------------

    def build_chunks(self, documents):
        """
        Splits each document into paragraph-like chunks.
        Returns a list of (filename, chunk_text).
        """
        chunks = []

        for filename, text in documents:
            paragraphs = text.split("\n\n")
            for paragraph in paragraphs:
                chunk = paragraph.strip()
                if chunk:
                    chunks.append((filename, chunk))

        return chunks

    # -----------------------------------------------------------
    # Index Construction (Phase 1)
    # -----------------------------------------------------------

    def build_index(self, chunks):
        """
        TODO (Phase 1):
        Build a tiny inverted index mapping lowercase words to the documents
        they appear in.

        Example structure:
        {
            "token": ["AUTH.md", "API_REFERENCE.md"],
            "database": ["DATABASE.md"]
        }

        Keep this simple: split on whitespace, lowercase tokens,
        ignore punctuation if needed.
        """
        index = {}
        punctuation = ".,!?;:\"'()[]{}"

        for chunk_id, (_, text) in enumerate(chunks):
            for raw_token in text.lower().split():
                token = raw_token.strip(punctuation)
                if not token:
                    continue

                if token not in index:
                    index[token] = []
                if chunk_id not in index[token]:
                    index[token].append(chunk_id)

        return index

    # -----------------------------------------------------------
    # Scoring and Retrieval (Phase 1)
    # -----------------------------------------------------------

    def _tokenize(self, text):
        punctuation = ".,!?;:\"'()[]{}"
        tokens = []

        for raw_token in text.lower().split():
            token = raw_token.strip(punctuation)
            if token:
                tokens.append(token)

        return tokens

    def _query_keywords(self, query):
        keywords = []
        for token in self._tokenize(query):
            if len(token) >= 3 and token not in self.STOPWORDS:
                keywords.append(token)
        return keywords

    def score_document(self, query, text):
        """
        TODO (Phase 1):
        Return a simple relevance score for how well the text matches the query.

        Suggested baseline:
        - Convert query into lowercase words
        - Count how many appear in the text
        - Return the count as the score
        """
        query_tokens = self._query_keywords(query)
        if not query_tokens:
            return 0

        text_tokens = set(self._tokenize(text))

        score = 0
        for token in query_tokens:
            if token in text_tokens:
                score += 1

        return score

    def retrieve(self, query, top_k=3):
        """
        TODO (Phase 1):
        Use the index and scoring function to select top_k relevant document snippets.

        Return a list of (filename, text) sorted by score descending.
        """
        scored_results = self._retrieve_with_scores(query, top_k=top_k)
        return [(filename, text) for filename, text, _ in scored_results]

    def _retrieve_with_scores(self, query, top_k=3):
        """
        Internal helper that returns scored snippets as
        (filename, text, score).
        """
        query_tokens = set(self._query_keywords(query))
        if not query_tokens:
            return []

        candidate_chunk_ids = set()
        for token in query_tokens:
            if token in self.index:
                candidate_chunk_ids.update(self.index[token])

        results = []
        for chunk_id in candidate_chunk_ids:
            filename, text = self.chunks[chunk_id]

            score = self.score_document(query, text)
            if score > 0:
                results.append((filename, text, score))

        results.sort(key=lambda item: item[2], reverse=True)

        return results[:top_k]

    def _has_useful_context(self, scored_snippets):
        """
        Balanced refusal guardrail for retrieval-only mode.

        Useful context means:
        - at least one snippet has score >= 2
        - average score is >= 1.0
        """
        if not scored_snippets:
            return False

        scores = [score for _, _, score in scored_snippets]
        has_strong_snippet = any(score >= 2 for score in scores)
        average_score = sum(scores) / len(scores)

        return has_strong_snippet and average_score >= 1.0

    # -----------------------------------------------------------
    # Answering Modes
    # -----------------------------------------------------------

    def answer_retrieval_only(self, query, top_k=3):
        """
        Phase 1 retrieval only mode.
        Returns raw snippets and filenames with no LLM involved.
        """
        scored_snippets = self._retrieve_with_scores(query, top_k=top_k)

        if not self._has_useful_context(scored_snippets):
            return "I do not know based on these docs."

        formatted = []
        snippets = [(filename, text) for filename, text, _ in scored_snippets]
        for filename, text in snippets:
            formatted.append(f"[{filename}]\n{text}\n")

        return "\n---\n".join(formatted)

    def answer_rag(self, query, top_k=3):
        """
        Phase 2 RAG mode.
        Uses student retrieval to select snippets, then asks Gemini
        to generate an answer using only those snippets.
        """
        if self.llm_client is None:
            raise RuntimeError(
                "RAG mode requires an LLM client. Provide a GeminiClient instance."
            )

        snippets = self.retrieve(query, top_k=top_k)

        if not snippets:
            return "I do not know based on these docs."

        return self.llm_client.answer_from_snippets(query, snippets)

    # -----------------------------------------------------------
    # Bonus Helper: concatenated docs for naive generation mode
    # -----------------------------------------------------------

    def full_corpus_text(self):
        """
        Returns all documents concatenated into a single string.
        This is used in Phase 0 for naive 'generation only' baselines.
        """
        return "\n\n".join(text for _, text in self.documents)
