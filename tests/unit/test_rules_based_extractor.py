from munipal.services.extraction.rules_based_extractor import RulesBasedExtractor


def test_rules_based_extractor_extracts_labelled_money_party_and_location_with_provenance():
    extractor = RulesBasedExtractor()

    chunks = [
        {
            "id": "chunk-1",
            "text_content": "Borrower: Oakport Health System\nProject location: Alameda County, California",
        },
        {
            "id": "chunk-2",
            "text_content": "Total Project Cost: $42.5 million\nMinimum DSCR Covenant: 1.25x",
        },
    ]

    facts = extractor.extract(
        chunks,
        [
            "parties.borrower.name",
            "project.location.jurisdiction",
            "capital.project-cost",
            "finmodel.inputs.dscr.minimum",
        ],
    )

    by_path = {fact.schema_path: fact for fact in facts}

    assert by_path["parties.borrower.name"].value == "Oakport Health System"
    assert by_path["parties.borrower.name"].chunk_id == "chunk-1"
    assert by_path["parties.borrower.name"].source_quote == "Borrower: Oakport Health System"
    assert by_path["project.location.jurisdiction"].value == "Alameda County, California"
    assert by_path["capital.project-cost"].value == 42500000
    assert by_path["capital.project-cost"].value_type == "currency"
    assert by_path["capital.project-cost"].unit == "USD"
    assert by_path["capital.project-cost"].chunk_id == "chunk-2"
    assert by_path["finmodel.inputs.dscr.minimum"].value == 1.25


def test_rules_based_extractor_only_extracts_explicit_matching_paths():
    extractor = RulesBasedExtractor()

    facts = extractor.extract(
        [{"id": "chunk-1", "text_content": "The sponsor expects strong market demand."}],
        ["capital.project-cost", "parties.sponsor.name"],
    )

    assert facts == []


def test_rules_based_extractor_pairs_label_lines_for_healthcare_uploads():
    extractor = RulesBasedExtractor()

    facts = extractor.extract(
        [
            {
                "id": "license-chunk",
                "text_content": (
                    "Hospital Operating License\n"
                    "Facility Name:\n"
                    "Oakport Regional Medical Center\n"
                    "License Number:\n"
                    "LIC-770487\n"
                    "Licensed Beds:\n"
                    "425\n"
                ),
            }
        ],
        ["project.name", "healthcare.licensure", "healthcare.utilization.trend"],
    )

    by_path = {fact.schema_path: fact for fact in facts}
    assert by_path["project.name"].value == "Oakport Regional Medical Center"
    assert by_path["healthcare.licensure"].value == "LIC-770487"
    assert by_path["healthcare.utilization.trend"].value == "425"
