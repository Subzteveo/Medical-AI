"""Bounded linguistic engineering cases, not adjudicated clinical examples."""
import pytest
from medical_ai.planner import classify_consequence, plan_query
from medical_ai.schemas import AnswerStatus, ConsequenceLevel
from medical_ai.engine import EvidenceEngine
from test_pubmed_context import FixtureConnector, xml_abstract

# id, text, drug_interaction expected, other category, reason
CASES = [
 ('variables', 'Interactions between mindfulness and attention were examined.', False, None, 'Explicit non-pharmacological operands'),
 ('statistics', 'The age-by-sex interaction was significant.', False, None, 'Explicit demographic statistical factors'),
 ('negated-statistics', 'No interaction between education and income was found.', False, None, 'Negation does not change the resolved operands'),
 ('anaphora', 'Stress, resilience and social support were measured. The interactions of these variables were examined.', False, None, 'Complete immediately preceding variable enumeration'),
 ('grouped-anaphora', "Students’ stress, protective factors (e.g. resilience, social support, mindfulness and self-efficacy) and psychological well-being (PWB) have been reported. However, the interactions of these variables were examined.", False, None, 'Grouped enumeration, abbreviation and e.g. stay intact'),
 ('unknown-variables', 'X and Y were measured. The interactions of these variables were examined.', True, None, 'Unknown antecedents may be medicines'),
 ('unknown-statistics', 'Statistical interactions were significant.', True, None, 'Statistical alone does not establish non-drug operands'),
 ('misleading-reference', 'Stress and resilience were measured. Clarithromycin and simvastatin showed interactions of these variables.', True, None, 'An intervening subject makes the reference unresolved'),
 ('shared-semicolon', 'Interactions between attention and mindfulness; and clarithromycin and simvastatin were examined.', True, None, 'A semicolon is not proof that a shared operand list ended'),
 ('drug', 'Drug interactions were examined.', True, None, 'Explicit medicines context'),
 ('named', 'Interactions between clarithromycin and simvastatin were examined.', True, None, 'Unresolved operands stay high without a drug-name dictionary'),
 ('novel-names', 'Interactions between investigational compound ZX17 and QY42 were examined.', True, None, 'Unknown compounds remain conservative'),
 ('verb', 'Fluconazole interacts with tacrolimus.', True, None, 'Existing verbal interaction detection retained'),
 ('negated-drug', 'No interaction between clarithromycin and simvastatin was observed.', True, None, 'A negative medicine-safety assertion still needs verification'),
 ('across-sentences', 'Clarithromycin and simvastatin were assessed. Their interaction was significant.', True, None, 'Unresolved cross-sentence reference'),
 ('mixed-sentences', 'Interactions between attention and mindfulness were examined. Fluconazole interacts with tacrolimus.', True, None, 'One benign mention cannot suppress another'),
 ('mixed-clause', 'Interactions between attention and mindfulness and between fluconazole and tacrolimus were examined.', True, None, 'Mixed operands in one mention'),
 ('mixed-list', 'Interactions between attention, mindfulness and tacrolimus were examined.', True, None, 'Entire operand list must resolve'),
 ('mixed-semicolon', 'Interactions between attention and mindfulness; interactions between clarithromycin and simvastatin.', True, None, 'Every mention must resolve'),
 ('ambiguous', 'No interactions were found.', True, None, 'Negation is not proof of benign meaning'),
 ('ambiguous-reference', 'Attention was assessed. These interactions were significant.', True, None, 'Unresolved reference'),
 ('ambiguous-antecedent', 'Stress and investigational treatment were measured. Interactions of these variables were examined.', True, None, 'Incomplete non-drug enumeration'),
 ('distant-reference', 'Stress and resilience were measured. Two medicines were assessed. Interactions of these variables were examined.', True, None, 'Do not skip the nearest antecedent'),
 ('pharmacological-modifier', 'Drug interactions between attention and mindfulness were examined.', True, None, 'Explicit pharmacology overrides apparent benign operands'),
 ('pharmacological-context', 'Tacrolimus medication was assessed. Interactions between age and sex were examined.', True, None, 'Explicit pharmacological context conservatively prevents exemption'),
 ('dose', 'Interactions between attention and mindfulness were examined. Dose adjustment was discussed.', False, 'medication_dose', 'Other high-consequence checks remain independent'),
 ('pregnancy', 'Interactions between attention and mindfulness were examined during pregnancy.', False, 'pregnancy', 'Other high-consequence checks remain independent'),
 ('paediatric', 'Interactions between attention and mindfulness were examined in children.', False, 'paediatrics', 'Complete population context retained'),
 ('anticoagulation', 'Interactions between attention and mindfulness were examined. Warfarin was discussed.', False, 'anticoagulation', 'Separate high-consequence category remains high'),
]

@pytest.mark.parametrize('case,text,interaction,other,reason', CASES, ids=[c[0] for c in CASES])
def test_query_classification(case,text,interaction,other,reason):
    level, categories = classify_consequence(text)
    assert ('drug_interaction' in categories) is interaction, reason
    assert level == (ConsequenceLevel.HIGH if interaction or other else ConsequenceLevel.MODERATE), reason
    if other: assert other in categories
    plan = plan_query('Find literature about ' + text)
    assert plan.consequence_level == level
    assert plan.required_second_pass is (level == ConsequenceLevel.HIGH)
    assert ('HIGH_CONSEQUENCE:drug_interaction' in plan.safety_flags) is interaction

@pytest.mark.parametrize('case,text,interaction,other,reason', CASES, ids=[c[0] for c in CASES])
async def test_complete_abstract_classification(case,text,interaction,other,reason):
    # Low-consequence query means these gates must come from the full abstract.
    abstract = 'Mindfulness and attention were assessed. ' + text
    out = await EvidenceEngine(FixtureConnector(xml_abstract(('RESULTS', abstract)))).answer('Find literature about mindfulness and attention')
    if interaction or other:
        assert out.status == AnswerStatus.HIGH_CONSEQUENCE_VERIFICATION_FAILED, reason
        assert not out.claims and not out.sources and not out.passages
        assert 'FAIL' in out.trace.verification_results.values()
    else:
        assert out.status == AnswerStatus.ANSWER_SUPPORTED_WITH_QUALIFICATIONS, reason
        assert [c.claim_text for c in out.claims] == ['RESULTS: ' + abstract]
        assert out.passages[0].text == 'RESULTS: ' + abstract
        assert out.sources[0].raw_metadata['abstract_labels'] == ['RESULTS']
        assert 'PubMed abstract' in out.answer_markdown

async def test_high_query_cannot_be_downgraded_by_benign_abstract():
    out = await EvidenceEngine(FixtureConnector(xml_abstract(('', 'Mindfulness and attention interactions between age and sex were examined.')))).answer('Find literature about mindfulness and drug interactions')
    assert out.status == AnswerStatus.HIGH_CONSEQUENCE_VERIFICATION_FAILED
    assert not out.claims
