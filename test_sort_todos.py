import sys
from unittest.mock import patch, MagicMock

with patch.dict("os.environ", {"LIST_ID": "fake"}), \
     patch("auth.get_access_token", return_value="fake_token"):
    from sort_todos import (
        matches_template,
        extract_store_prefix,
        find_category_and_position,
        find_matching_position,
        ALDI,
        EDEKA,
    )


class TestMatchesTemplate:
    def test_exact_match(self):
        assert matches_template("Joghurt", "Joghurt")

    def test_case_insensitive(self):
        assert matches_template("joghurt", "Joghurt")

    def test_with_leading_spaces(self):
        assert matches_template("  Joghurt  ", "Joghurt")

    def test_quantity_prefix(self):
        assert matches_template("2 Joghurt", "Joghurt")

    def test_quantity_x_prefix(self):
        assert matches_template("2x Joghurt", "Joghurt")

    def test_quantity_suffix(self):
        assert matches_template("Joghurt 3x", "Joghurt")

    def test_free_suffix_matches(self):
        assert matches_template("Joghurt Natur", "Joghurt")

    def test_placeholder_suffix_matches(self):
        assert matches_template("Joghurt X", "Joghurt")

    def test_price_suffix(self):
        assert matches_template("Joghurt 2,49", "Joghurt")

    def test_price_euro_suffix(self):
        assert matches_template("Joghurt 2,49€", "Joghurt")

    def test_price_euro_space_suffix(self):
        assert matches_template("Joghurt 2,49 €", "Joghurt")

    def test_no_match(self):
        assert not matches_template("Milch", "Joghurt")

    def test_partial_no_match(self):
        assert not matches_template("Joghurteis", "Joghurt")

    def test_template_with_spaces(self):
        assert matches_template("Passierte Tomaten", "Passierte Tomaten")

    def test_template_with_special_chars(self):
        assert matches_template("Aldi Hähnchen-/Putenaufschnitt", "Aldi Hähnchen-/Putenaufschnitt")


class TestExtractStorePrefix:
    def test_edeka_prefix(self):
        store, rest = extract_store_prefix("Edeka Bionade")
        assert store == "edeka"
        assert rest == "Bionade"

    def test_aldi_prefix(self):
        store, rest = extract_store_prefix("Aldi Schoki")
        assert store == "aldi"
        assert rest == "Schoki"

    def test_no_prefix(self):
        store, rest = extract_store_prefix("Joghurt")
        assert store is None
        assert rest == "Joghurt"

    def test_prefix_case_insensitive(self):
        store, rest = extract_store_prefix("edeka Bionade")
        assert store == "edeka"
        assert rest == "Bionade"

    def test_prefix_without_space_no_match(self):
        store, rest = extract_store_prefix("EdekaBionade")
        assert store is None

    def test_preserves_rest_casing(self):
        store, rest = extract_store_prefix("Edeka TK Laugenstangen")
        assert rest == "TK Laugenstangen"


class TestFindCategoryAndPosition:
    def test_aldi_item(self):
        cat, pos = find_category_and_position("Bananen")
        assert cat == "aldi"
        assert pos == 1

    def test_edeka_item(self):
        cat, pos = find_category_and_position("Bionade")
        assert cat == "edeka"
        assert pos == 1

    def test_unknown_item(self):
        cat, pos = find_category_and_position("Fischstäbchen")
        assert cat == "unsortiert"

    def test_edeka_prefix_with_edeka_item(self):
        cat, pos = find_category_and_position("Edeka Bionade")
        assert cat == "edeka"
        assert pos == 1

    def test_aldi_prefix_overrides_edeka_list(self):
        cat, pos = find_category_and_position("Aldi Bionade")
        assert cat == "aldi"
        assert pos == -1

    def test_edeka_prefix_unknown_item(self):
        cat, pos = find_category_and_position("Edeka Fischstäbchen")
        assert cat == "edeka"
        assert pos == -1

    def test_aldi_prefix_unknown_item(self):
        cat, pos = find_category_and_position("Aldi Fischstäbchen")
        assert cat == "aldi"
        assert pos == -1

    def test_aldi_prefix_with_aldi_item(self):
        cat, pos = find_category_and_position("Aldi Schoki")
        assert cat == "aldi"
        assert pos == 19

    def test_quantity_prefix(self):
        cat, pos = find_category_and_position("2x Bananen")
        assert cat == "aldi"
        assert pos == 1

    def test_edeka_prefix_with_quantity(self):
        cat, pos = find_category_and_position("Edeka 2x Bionade")
        assert cat == "edeka"
        assert pos == 1


class TestGoudaPrefixParity:
    """"Aldi Gouda [X]" muss exakt wie "Gouda [X]" sortiert werden."""

    SUFFIXES = ["", " 3x", " 2,49 €", " X", " gerieben"]

    def test_prefixed_matches_unprefixed(self):
        for suffix in self.SUFFIXES:
            plain = find_category_and_position(f"Gouda{suffix}")
            prefixed = find_category_and_position(f"Aldi Gouda{suffix}")
            assert plain == prefixed, f"Abweichung bei Suffix {suffix!r}"
            assert plain[0] == "aldi"

    def test_quantity_prefix_parity(self):
        assert find_category_and_position("Aldi 2x Gouda") == find_category_and_position("Gouda")


class TestStoreAliasGG:
    def test_gg_is_edeka_prefix(self):
        store, rest = extract_store_prefix("GG Fischstäbchen")
        assert store == "edeka"
        assert rest == "Fischstäbchen"

    def test_gg_prefix_case_insensitive(self):
        store, _ = extract_store_prefix("gg Fischstäbchen")
        assert store == "edeka"

    def test_gg_prefix_with_known_item(self):
        assert find_category_and_position("GG Milch") == find_category_and_position("Milch")

    def test_gg_prefix_unknown_item(self):
        cat, pos = find_category_and_position("GG Fischstäbchen")
        assert cat == "edeka"
        assert pos == -1

    def test_gg_prefix_overrides_aldi_list(self):
        cat, pos = find_category_and_position("GG Gouda")
        assert cat == "edeka"
        assert pos == -1

    def test_gg_without_space_no_match(self):
        store, _ = extract_store_prefix("GGMilch")
        assert store is None

    def test_list_entry_beats_gg_prefix(self):
        """"GG Oliven" ist ein echter Listeneintrag und behält seine Position."""
        cat, pos = find_category_and_position("GG Oliven")
        assert cat == "edeka"
        assert pos == EDEKA.index("GG Oliven")

    def test_gg_suffix_entry_unaffected(self):
        cat, pos = find_category_and_position("Roggen Vollkornbrot GG")
        assert cat == "edeka"
        assert pos == EDEKA.index("Roggen Vollkornbrot GG")


class TestLongestMatchWins:
    """Der freie Zusatz darf spezifischere Einträge nicht schlucken."""

    def test_reis_hellblau_beats_reis(self):
        assert find_category_and_position("Reis hellblau")[1] == ALDI.index("Reis hellblau")

    def test_plain_reis_still_matches(self):
        assert find_category_and_position("Reis")[1] == ALDI.index("Reis")

    def test_kaesepapier_beats_kaese(self):
        assert find_category_and_position("Käsepapier")[1] == EDEKA.index("Käsepapier")

    def test_koerniger_frischkaese(self):
        assert find_category_and_position("körniger Frischkäse")[1] == EDEKA.index("körniger Frischkäse")

    def test_no_match_returns_none(self):
        assert find_matching_position(["Milch"], "Fischstäbchen") is None


class TestNoFalsePositives:
    def test_substring_without_space_no_match(self):
        assert find_category_and_position("Joghurteis") == ("unsortiert", 0)

    def test_unknown_item_stays_unsorted(self):
        assert find_category_and_position("Fischstäbchen") == ("unsortiert", 0)
