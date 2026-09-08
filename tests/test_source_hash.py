from scripts.build_offer_snapshot import SourceSpec, source_hash


def test_source_hash_is_independent_of_checkout_path(tmp_path):
    digests = []
    for checkout_name in ("developer-checkout", "github-runner-checkout"):
        catalogue_dir = tmp_path / checkout_name / "data" / "source"
        source = catalogue_dir / "platform" / "offers.csv"
        source.parent.mkdir(parents=True)
        source.write_text("offer_id,platform_id\nONE,PLATFORM_A\n")
        specs = [SourceSpec(source, "csv", "", "")]
        digests.append(source_hash(specs, catalogue_dir))

    assert digests[0] == digests[1]


def test_source_hash_changes_with_relative_name_or_content(tmp_path):
    catalogue_dir = tmp_path / "data" / "source"
    first = catalogue_dir / "one.csv"
    second = catalogue_dir / "two.csv"
    catalogue_dir.mkdir(parents=True)
    first.write_text("same")
    second.write_text("same")

    first_hash = source_hash([SourceSpec(first, "csv", "", "")], catalogue_dir)
    renamed_hash = source_hash([SourceSpec(second, "csv", "", "")], catalogue_dir)
    second.write_text("changed")
    changed_hash = source_hash([SourceSpec(second, "csv", "", "")], catalogue_dir)

    assert first_hash != renamed_hash
    assert renamed_hash != changed_hash
