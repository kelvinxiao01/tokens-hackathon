from pydantic import BaseModel, Field


class ICP(BaseModel):
    industries: list[str] = Field(description="Industries or verticals the product targets.")
    company_size: str = Field(description="Typical company size, e.g. 'Series A', '50-500 employees'.")
    geographies: list[str] = Field(default_factory=list, description="Target geographies. Empty = global.")
    target_roles: list[str] = Field(description="Decision-maker roles, e.g. 'Head of Sales'.")
    pain_signals: list[str] = Field(description="Observable signals a prospect has the pain this product solves.")
    search_queries: list[str] = Field(description="3-5 web search queries to discover candidate companies.")


class ProspectCandidate(BaseModel):
    name: str
    homepage_url: str
    one_liner: str


class CandidateList(BaseModel):
    candidates: list[ProspectCandidate]


class ScrapedDoc(BaseModel):
    url: str
    title: str
    content: str


class ResearchOutput(BaseModel):
    docs: list[ScrapedDoc]


class ProspectDossier(BaseModel):
    prospect_name: str
    homepage_url: str
    what_they_do: str
    decision_makers: list[str] = Field(description="Names + roles of likely decision-makers found in research.")
    pain_signals_found: list[str]
    fit_score: int = Field(ge=0, le=10)
    fit_rationale: str
    citations: list[str] = Field(description="URLs supporting the claims above.")


class CallBrief(BaseModel):
    prospect_name: str
    opener: str
    value_prop: str
    discovery_questions: list[str]
    likely_objections: list[str]
    next_step_ask: str
    citations: list[str]
