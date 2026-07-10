from report.generate import EVIDENCE_TYPE_GUIDE, LIMITATIONS_PARAGRAPH, build_report_payload, render_html, render_markdown


def test_target_report_carries_standard_limitations_paragraph(golden_cards):
    payload = build_report_payload(golden_cards, dataset_id="test", top_n=2)

    assert payload["limitations"] == LIMITATIONS_PARAGRAPH
    assert "primary human CD4⁺ T cell CRISPRi Perturb-seq" in payload["limitations"]
    assert "Rest/Stim8hr/Stim48hr" in payload["limitations"]
    assert "independent guides" in payload["limitations"]
    assert "disease-context models" in payload["limitations"]

    markdown = render_markdown(payload)
    html = render_html(payload)
    assert "## Limitations" in markdown
    assert LIMITATIONS_PARAGRAPH in markdown
    assert "<h2>Limitations</h2>" in html
    assert LIMITATIONS_PARAGRAPH in html


def test_target_report_carries_evidence_type_guide(golden_cards):
    payload = build_report_payload(golden_cards, dataset_id="test", top_n=2)

    assert payload["evidence_type_guide"] == EVIDENCE_TYPE_GUIDE
    labels = {item["label"] for item in payload["evidence_type_guide"]}
    assert labels == {
        "Perturb-seq screen evidence",
        "Human genetic association",
        "Population LoF evidence",
        "Drug / tractability precedent",
        "Heuristic readiness triage",
    }

    markdown = render_markdown(payload)
    html = render_html(payload)
    assert "## Evidence Type Guide" in markdown
    assert "<h2>Evidence Type Guide</h2>" in html
    assert "not therapeutic efficacy" in markdown
    assert "not a clinical recommendation" in html
