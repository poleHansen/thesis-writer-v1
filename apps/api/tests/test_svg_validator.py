from __future__ import annotations

from pathlib import Path

from app.services.svg_validator import SvgValidator


def test_validator_accepts_xmlns_and_fill_opacity() -> None:
    svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1280\" height=\"720\" viewBox=\"0 0 1280 720\">\n+  <rect width=\"1280\" height=\"720\" fill=\"#ffffff\" />\n+  <text x=\"80\" y=\"120\" fill=\"#111827\" fill-opacity=\"0.72\">Normal content</text>\n+</svg>"""

    result = SvgValidator().validate_file("slide-01.svg", svg_content)

    assert result.is_valid is True
    assert result.issues == []


def test_validator_rejects_group_opacity_and_external_href() -> None:
    svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1280\" height=\"720\" viewBox=\"0 0 1280 720\">\n+  <g opacity=\"0.5\"><rect width=\"100\" height=\"100\" /></g>\n+  <image href=\"https://example.com/image.png\" x=\"0\" y=\"0\" width=\"100\" height=\"100\" />\n+</svg>"""

    result = SvgValidator().validate_file("slide-02.svg", svg_content)

    assert result.is_valid is False
    assert "banned_attribute_token:group_opacity" in result.issues
    assert "external_resource_reference" in result.issues


def test_validator_rejects_missing_local_resource(tmp_path: Path) -> None:
    svg_path = tmp_path / "slide-03.svg"
    svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1280\" height=\"720\" viewBox=\"0 0 1280 720\">\n  <image href=\"images/chart.png\" x=\"0\" y=\"0\" width=\"120\" height=\"120\" />\n</svg>"""

    result = SvgValidator().validate_file(str(svg_path), svg_content)

    assert result.is_valid is False
    assert "missing_local_resource_reference" in result.issues


def test_validator_accepts_existing_local_resource(tmp_path: Path) -> None:
    svg_path = tmp_path / "slide-04.svg"
    image_dir = tmp_path / "images"
    image_dir.mkdir()
    (image_dir / "chart.png").write_bytes(b"png")
    svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1280\" height=\"720\" viewBox=\"0 0 1280 720\">\n  <image href=\"images/chart.png\" x=\"0\" y=\"0\" width=\"120\" height=\"120\" />\n</svg>"""

    result = SvgValidator().validate_file(str(svg_path), svg_content)

    assert result.is_valid is True
    assert "missing_local_resource_reference" not in result.issues


def test_validator_rejects_text_that_exceeds_canvas_width() -> None:
    long_title = "A" * 80
    svg_content = f"""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1280\" height=\"720\" viewBox=\"0 0 1280 720\">\n  <text x=\"1180\" y=\"160\" font-size=\"32\">{long_title}</text>\n</svg>"""

    result = SvgValidator().validate_file("slide-05.svg", svg_content)

    assert result.is_valid is False
    assert "potential_text_overflow" in result.issues


def test_validator_rejects_centered_text_that_spills_off_canvas() -> None:
    centered_text = "Centered text " * 8
    svg_content = f"""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1280\" height=\"720\" viewBox=\"0 0 1280 720\">\n  <text x=\"640\" y=\"400\" text-anchor=\"middle\" font-size=\"44\">{centered_text}</text>\n</svg>"""

    result = SvgValidator().validate_file("slide-06.svg", svg_content)

    assert result.is_valid is False
    assert "potential_text_overflow" in result.issues


def test_validator_rejects_text_exceeding_declared_card_width() -> None:
    card_body = "Card body text " * 10
    svg_content = f"""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1280\" height=\"720\" viewBox=\"0 0 1280 720\">\n  <text x=\"104\" y=\"366\" font-size=\"18\" data-max-width=\"220\">{card_body}</text>\n</svg>"""

    result = SvgValidator().validate_file("slide-07.svg", svg_content)

    assert result.is_valid is False
    assert "potential_text_overflow" in result.issues


def test_validator_accepts_text_within_canvas_and_declared_width() -> None:
    svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1280\" height=\"720\" viewBox=\"0 0 1280 720\">\n  <text x=\"80\" y=\"160\" font-size=\"24\">Short title</text>\n  <text x=\"640\" y=\"400\" text-anchor=\"middle\" font-size=\"28\">Closing summary</text>\n  <text x=\"104\" y=\"366\" font-size=\"18\" data-max-width=\"320\">Compact card copy</text>\n</svg>"""

    result = SvgValidator().validate_file("slide-08.svg", svg_content)

    assert result.is_valid is True
    assert "potential_text_overflow" not in result.issues


def test_validator_rejects_text_exceeding_declared_height() -> None:
    svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1280\" height=\"720\" viewBox=\"0 0 1280 720\">\n  <text x=\"104\" y=\"320\" font-size=\"18\" data-max-width=\"220\" data-max-height=\"24\">First line<tspan x=\"104\" dy=\"21.6\">Second line</tspan></text>\n</svg>"""

    result = SvgValidator().validate_file("slide-09.svg", svg_content)

    assert result.is_valid is False
    assert "potential_text_overflow" in result.issues


def test_validator_rejects_single_line_text_exceeding_declared_height() -> None:
    svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1280\" height=\"720\" viewBox=\"0 0 1280 720\">\n  <text x=\"80\" y=\"170\" font-size=\"38\" data-max-width=\"1120\" data-max-height=\"30\">Wrapped title</text>\n</svg>"""

    result = SvgValidator().validate_file("slide-10.svg", svg_content)

    assert result.is_valid is False
    assert "potential_text_overflow" in result.issues


def test_validator_accepts_single_line_text_with_sufficient_height() -> None:
    svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1280\" height=\"720\" viewBox=\"0 0 1280 720\">\n  <text x=\"80\" y=\"685\" font-size=\"18\" data-max-width=\"1120\" data-max-height=\"22\">7/12 Technology Grid</text>\n</svg>"""

    result = SvgValidator().validate_file("slide-11.svg", svg_content)

    assert result.is_valid is True
    assert "potential_text_overflow" not in result.issues


def test_validator_respects_declared_line_height_for_multiline_text() -> None:
    svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1280\" height=\"720\" viewBox=\"0 0 1280 720\">\n  <text x=\"104\" y=\"320\" font-size=\"18\" data-max-width=\"220\" data-max-height=\"44\" data-line-height=\"1.2\">First line<tspan x=\"104\" dy=\"21.6\">Second line</tspan></text>\n</svg>"""

    result = SvgValidator().validate_file("slide-12.svg", svg_content)

    assert result.is_valid is True
    assert "potential_text_overflow" not in result.issues


def test_validator_falls_back_to_default_line_height_without_metadata() -> None:
    svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1280\" height=\"720\" viewBox=\"0 0 1280 720\">\n  <text x=\"104\" y=\"320\" font-size=\"18\" data-max-width=\"220\" data-max-height=\"40\">First line<tspan x=\"104\" dy=\"21.6\">Second line</tspan></text>\n</svg>"""

    result = SvgValidator().validate_file("slide-13.svg", svg_content)

    assert result.is_valid is False
    assert "potential_text_overflow" in result.issues


def test_validator_rejects_bullet_text_exceeding_sidebar_group_height() -> None:
    svg_content = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1280\" height=\"720\" viewBox=\"0 0 1280 720\">\n  <text x=\"884\" y=\"470\" font-size=\"18\" data-max-width=\"280\" data-max-height=\"44\" data-line-height=\"1.2\">Bullet label<tspan x=\"884\" dy=\"21.6\">Second line</tspan></text>\n  <text x=\"884\" y=\"525\" font-size=\"18\" data-max-width=\"280\" data-max-height=\"44\" data-line-height=\"1.2\">Overflowing bullet<tspan x=\"884\" dy=\"21.6\">Second line</tspan></text>\n</svg>"""

    result = SvgValidator().validate_file("slide-14.svg", svg_content)

    assert result.is_valid is True
    assert "potential_text_overflow" not in result.issues