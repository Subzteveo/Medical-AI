from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET

import httpx

from medical_ai.retrieval_query import normalize_search_query
from medical_ai.schemas import Passage, SourceRecord

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _text(node) -> str:
    return "" if node is None else "".join(node.itertext()).strip()


def _hash_id(prefix: str, value: str) -> str:
    return f"{prefix}_{hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]}"


class PubMedConnector:
    """PubMed ESearch + EFetch adapter for the evidence path."""
    name = "pubmed-eutils"
    version = "alpha2.1-red-remediation"
    source_class = "biomedical_literature"
    phi_approved = False

    def __init__(self, *, email: str | None = None, api_key: str | None = None, timeout: float = 20.0):
        self.email = email
        self.api_key = api_key
        self.timeout = timeout

    def _common(self) -> dict[str, str]:
        params = {"tool": "medical-ai-evidence-workbench"}
        if self.email:
            params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key
        return params

    async def search_and_fetch(self, query: str, limit: int = 5) -> tuple[list[SourceRecord], list[Passage]]:
        search_term = normalize_search_query(query)
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            search_params = {
                **self._common(),
                "db": "pubmed",
                "term": search_term,
                "retmode": "json",
                "retmax": str(limit),
                "sort": "relevance",
            }
            s = await client.get(f"{EUTILS}/esearch.fcgi", params=search_params)
            s.raise_for_status()
            ids = s.json().get("esearchresult", {}).get("idlist", [])
            if not ids:
                return [], []
            fetch_params = {
                **self._common(),
                "db": "pubmed",
                "id": ",".join(ids),
                "retmode": "xml",
            }
            f = await client.get(f"{EUTILS}/efetch.fcgi", params=fetch_params)
            f.raise_for_status()
            return self._parse_pubmed_xml(f.text)

    @staticmethod
    def _parse_pubmed_xml(xml_text: str) -> tuple[list[SourceRecord], list[Passage]]:
        root = ET.fromstring(xml_text)
        sources: list[SourceRecord] = []
        passages: list[Passage] = []
        for article in root.findall(".//PubmedArticle"):
            citation = article.find("MedlineCitation")
            if citation is None:
                continue
            pmid = _text(citation.find("PMID"))
            art = citation.find("Article")
            if art is None or not pmid:
                continue
            title = _text(art.find("ArticleTitle")) or f"PubMed {pmid}"
            journal = _text(art.find("Journal/Title"))
            pubdate = art.find("Journal/JournalIssue/PubDate")
            year = _text(pubdate.find("Year")) if pubdate is not None else None
            medline_date = _text(pubdate.find("MedlineDate")) if pubdate is not None else None
            publication_date = year or medline_date or None

            publication_types = [
                _text(node)
                for node in art.findall("PublicationTypeList/PublicationType")
                if _text(node)
            ]
            correction_types = [
                node.attrib.get("RefType", "")
                for node in citation.findall("CommentsCorrectionsList/CommentsCorrections")
                if node.attrib.get("RefType")
            ]
            retracted = (
                any(pt.lower() == "retracted publication" for pt in publication_types)
                or any(rt.lower() in {"retractionin", "retractionof"} for rt in correction_types)
            )

            identifiers = {"PMID": pmid}
            for aid in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
                kind = aid.attrib.get("IdType", "").upper()
                val = _text(aid)
                if kind and val:
                    identifiers[kind] = val

            source_id = f"pubmed:{pmid}"
            source = SourceRecord(
                source_id=source_id,
                authority="NLM/NCBI PubMed",
                publisher="U.S. National Library of Medicine / indexed publisher",
                source_type="indexed_biomedical_literature",
                title=title,
                jurisdiction="INTERNATIONAL",
                record_id=pmid,
                stable_url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                identifiers=identifiers,
                publication_date=publication_date,
                superseded=retracted,
                provenance_complete=True,
                raw_metadata={
                    "journal": journal,
                    "publication_types": publication_types,
                    "correction_types": correction_types,
                    "retracted": retracted,
                },
            )
            sources.append(source)

            passages.append(Passage(
                passage_id=_hash_id("passage", f"{source_id}:title:{title}"),
                source_id=source_id,
                section="TITLE",
                text=title,
                locator="ArticleTitle",
            ))
            for idx, abstract in enumerate(art.findall("Abstract/AbstractText")):
                text = _text(abstract)
                if not text:
                    continue
                label = abstract.attrib.get("Label") or abstract.attrib.get("NlmCategory") or "ABSTRACT"
                passages.append(Passage(
                    passage_id=_hash_id("passage", f"{source_id}:{idx}:{text}"),
                    source_id=source_id,
                    section=label,
                    text=text,
                    locator=f"AbstractText[{idx}]",
                ))
        return sources, passages
