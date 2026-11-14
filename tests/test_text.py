"""Text nodes: whitespace, fonts, baseline shifts and tspans."""

import pytest
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth

from tests.utils import (
    drawing_from_svg,
)


def rendered_span(string):
    """The left and right edge a String gets when rendered."""
    width = stringWidth(string.text, string.fontName, string.fontSize)
    if string.textAnchor == "middle":
        return string.x - width / 2, string.x + width / 2
    if string.textAnchor == "end":
        return string.x - width, string.x
    return string.x, string.x + width


class TestTextNode:
    def test_space_preservation(self):
        drawing = drawing_from_svg(
            """
            <?xml version="1.0"?>
            <svg width="777" height="267">
              <text style="fill:#000000; stroke:none; font-size:28;">
                <tspan>TITLE    1</tspan>
                <tspan x="-10.761" y="33.487">Subtitle</tspan>
              </text>
            </svg>
        """
        )
        main_group = drawing.contents[0]
        # By default, only two tspans produce String objects + 1 for the space
        # *between tspans, the start/end spaces/newlines are ignored.
        assert len(main_group.contents[0].contents) == 3
        assert main_group.contents[0].contents[0].text == "TITLE 1"

        drawing = drawing_from_svg(
            """
            <?xml version="1.0"?>
            <svg width="777" height="267" xml:space="preserve">
              <text style="fill:#000000; stroke:none; font-size:28;">
                <tspan>TITLE    1</tspan>
                <tspan x="-10.761" y="33.487">Subtitle</tspan>
              </text>
            </svg>
        """
        )
        main_group = drawing.contents[0]
        assert main_group.contents[0].contents[0].text == "     "
        assert main_group.contents[0].contents[1].text == "TITLE    1"

        drawing = drawing_from_svg(
            """
            <?xml version="1.0"?>
            <svg width="777" height="267">
              <text style="fill:#000000; stroke:none; font-size:28;">
                <tspan>TITLE    1</tspan>
                <tspan x="-10.761" y="33.487">Subtitle</tspan>
              </text>
              <text xml:space="preserve">  with   spaces </text>
            </svg>
        """
        )
        main_group = drawing.contents[0]
        # xml:space can be overriden per text node
        assert main_group.contents[0].contents[0].text == "TITLE 1"
        assert main_group.contents[1].contents[0].text == "  with   spaces "

    def test_font_shorthand(self):
        """The CSS `font` shorthand sets style, weight, size and family (#343)."""
        drawing = drawing_from_svg(
            """
            <svg viewBox="0 0 240 40" xmlns="http://www.w3.org/2000/svg">
              <style>
                text  { font: italic 12px serif; }
                tspan { font: bold 10px/1.2 sans-serif; fill: red; }
              </style>
              <text x="10" y="30">You are <tspan>not</tspan> a banana!</text>
              <text style="font: bold 20px monospace; font-size: 8px">x</text>
            </svg>
        """
        )
        strings = drawing.contents[0].contents[0].contents
        assert [(s.text, s.fontName, s.fontSize) for s in strings] == [
            ("You are ", "Times-Italic", 12),
            ("not", "Helvetica-Bold", 10),
            (" a banana!", "Times-Italic", 12),
        ]
        assert strings[1].fillColor == colors.red
        # A longhand after the shorthand still wins.
        last = drawing.contents[0].contents[1].contents[0]
        assert (last.fontName, last.fontSize) == ("Courier-Bold", 8)

    def test_font_size_keywords(self):
        """CSS font-size keywords are sizes, in the attribute and the shorthand."""
        drawing = drawing_from_svg(
            """
            <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
              <text font-size="medium">x</text>
              <text font-size="large">x</text>
              <text style="font-size: xx-small">x</text>
              <text style="font: bold x-large serif">x</text>
              <text font-size="larger">x</text>
            </svg>
        """
        )
        sizes = [text.contents[0].fontSize for text in drawing.contents[0].contents]
        assert sizes == [16, 18, 9, 24, 16 * 1.2]

    def test_invalid_font_shorthand_is_ignored(self):
        drawing = drawing_from_svg(
            """
            <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
              <text style="font-size: 20px; font: bold">x</text>
            </svg>
        """
        )
        string = drawing.contents[0].contents[0].contents[0]
        assert (string.fontName, string.fontSize) == ("Helvetica", 20)

    def test_relative_font_size_uses_parent_font_size(self):
        """Percent and em font sizes are relative to the parent's font size."""
        drawing = drawing_from_svg(
            """
            <svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">
              <g font-size="20">
                <text x="10" y="50">a<tspan style="font-size:70%">b</tspan><tspan
                      font-size="2em">c<tspan font-size="50%">d</tspan></tspan></text>
                <text x="10" y="80" font-size="150%">e</text>
              </g>
            </svg>
        """
        )
        texts = drawing.contents[0].contents[0].contents
        sizes = {s.text: s.fontSize for text in texts for s in text.contents}
        assert sizes == {"a": 20, "b": 14, "c": 40, "d": 20, "e": 30}

    def test_relative_font_size_keywords_use_parent_font_size(self):
        """``larger`` and ``smaller`` scale the parent's font size."""
        drawing = drawing_from_svg(
            """
            <svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">
              <g font-size="20">
                <text x="10" y="50">a<tspan font-size="larger">b</tspan><tspan
                      font-size="smaller">c</tspan></text>
              </g>
            </svg>
        """
        )
        texts = drawing.contents[0].contents[0].contents
        sizes = {s.text: s.fontSize for text in texts for s in text.contents}
        assert sizes["a"] == 20
        assert abs(sizes["b"] - 24) < 1e-9
        assert abs(sizes["c"] - 20 / 1.2) < 1e-9

    def test_baseline_shift_sources_and_units(self):
        drawing = drawing_from_svg(
            """
            <svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">
              <style>.up { baseline-shift: super }</style>
              <text x="10" y="50" font-size="20">a<tspan
                    style="baseline-shift: sub">b</tspan><tspan
                    baseline-shift="50%">c</tspan><tspan
                    class="up">d<tspan>e</tspan>f</tspan>g</text>
            </svg>
        """
        )
        strings = drawing.contents[0].contents[0].contents
        # The text group is flipped, so a String's y is minus its baseline.
        baselines = {s.text: -s.y for s in strings}
        assert baselines == {
            "a": 50,
            "b": 60,  # sub: half the font size down
            "c": 40,  # 50% of the font size up
            "d": 40,  # super from a <style> rule
            "e": 40,  # nested in the shifted tspan
            "f": 40,  # tail text inside the shifted tspan
            "g": 50,
        }

    def test_baseline_shift_is_not_inherited_from_group(self):
        drawing = drawing_from_svg(
            """
            <svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">
              <g baseline-shift="super">
                <text x="10" y="50" font-size="20">a<tspan>b</tspan></text>
              </g>
            </svg>
        """
        )
        strings = drawing.contents[0].contents[0].contents[0].contents
        assert {s.text: -s.y for s in strings} == {"a": 50, "b": 50}

    def test_tspan_position(self):
        """
        The x/y positions of a tspan are either relative to the current text
        position, or can be absoluted by specifying the x/y attributes.
        """
        drawing = drawing_from_svg(
            """
            <?xml version="1.0"?>
            <svg width="777" height="267">
              <text x="10" y="20" style="fill:#000000; stroke:none; font-size:28;">
                The start
                <tspan>TITLE 1</tspan>
                <!-- x position relative to current text position
                     y position offset in em -->
                <tspan dy="1.3em">(after title)</tspan>
                <!-- absolute position -->
                <tspan x="16.75" y="33.487">Subtitle</tspan>
                <!-- absolute position + shifting -->
                <tspan x="10" y="20" dx="3em" dy="1.5em">Complete</tspan>
                The end
              </text>
            </svg>
        """
        )
        main_group = drawing.contents[0]
        assert main_group.contents[0].contents[0].x == 10
        assert main_group.contents[0].contents[0].y == -20
        assert main_group.contents[0].contents[0].text == "The start "
        assert main_group.contents[0].contents[1].x > 10
        assert main_group.contents[0].contents[1].text == "TITLE 1"
        assert main_group.contents[0].contents[2].text == " "
        assert main_group.contents[0].contents[3].y == -20 - (1.3 * 28)
        assert main_group.contents[0].contents[3].text == "(after title)"
        assert main_group.contents[0].contents[4].text == " "
        assert main_group.contents[0].contents[5].x == 16.75
        assert main_group.contents[0].contents[5].y == -33.487
        assert main_group.contents[0].contents[5].text == "Subtitle"
        assert main_group.contents[0].contents[6].text == " "
        assert main_group.contents[0].contents[7].x == 10 + (3 * 28)
        assert main_group.contents[0].contents[7].y == -20 - (1.5 * 28)
        assert main_group.contents[0].contents[7].text == "Complete"
        assert main_group.contents[0].contents[8].text == " The end"


class TestLetterSpacing:
    def test_attribute_number(self):
        """A bare letter-spacing number spaces the characters out, one String
        per character, with no spacing after the last character."""
        drawing = drawing_from_svg(
            """
            <svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">
              <text x="10" y="50" font-size="20" letter-spacing="2">ABC</text>
            </svg>
        """
        )
        strings = drawing.contents[0].contents[0].contents
        assert [s.text for s in strings] == ["A", "B", "C"]
        wa, wb, wc = (stringWidth(c, "Helvetica", 20) for c in "ABC")
        assert [s.x for s in strings] == pytest.approx(
            [10, 10 + wa + 2, 10 + wa + wb + 4]
        )
        # The spacing only goes between characters: the right edge of the
        # last one is the start plus the bare width plus two spacings.
        right = strings[-1].x + wc
        assert right == pytest.approx(10 + stringWidth("ABC", "Helvetica", 20) + 4)

    def test_style_class_and_px(self):
        """letter-spacing works from a <style> class rule and with px units."""
        drawing = drawing_from_svg(
            """
            <svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">
              <style>.wide { letter-spacing: 3px }</style>
              <text x="10" y="50" font-size="20" class="wide">AB</text>
              <text x="10" y="80" font-size="20"
                    style="letter-spacing: 1px">CD</text>
            </svg>
        """
        )
        first, second = drawing.contents[0].contents
        wa = stringWidth("A", "Helvetica", 20)
        wc = stringWidth("C", "Helvetica", 20)
        assert [s.text for s in first.contents] == ["A", "B"]
        assert first.contents[1].x == pytest.approx(10 + wa + 3)
        assert [s.text for s in second.contents] == ["C", "D"]
        assert second.contents[1].x == pytest.approx(10 + wc + 1)

    def test_inherited_and_em(self):
        """letter-spacing is inherited; em resolves against the font size of
        the element the value is found on."""
        drawing = drawing_from_svg(
            """
            <svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">
              <g letter-spacing="0.5em" font-size="20">
                <text x="10" y="50">AB</text>
                <text x="10" y="80" font-size="40">CD</text>
              </g>
              <text x="10" y="110" font-size="20"
                    letter-spacing="0.5em">EF</text>
            </svg>
        """
        )
        group = drawing.contents[0].contents[0]
        inherited, own_size, direct = (
            group.contents[0],
            group.contents[1],
            drawing.contents[0].contents[1],
        )
        # 0.5em of the <g> font size (20) = 10, also for the 40px text.
        assert inherited.contents[1].x == pytest.approx(
            10 + stringWidth("A", "Helvetica", 20) + 10
        )
        assert own_size.contents[1].x == pytest.approx(
            10 + stringWidth("C", "Helvetica", 40) + 10
        )
        # 0.5em of the element's own font size (20) = 10.
        assert direct.contents[1].x == pytest.approx(
            10 + stringWidth("E", "Helvetica", 20) + 10
        )

    def test_tspan_overrides_and_tail_text(self):
        """Each fragment uses its own resolved spacing; tail text continues
        the chunk with the spacing of the <text> element."""
        drawing = drawing_from_svg(
            """
            <svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">
              <text x="10" y="50" font-size="20" letter-spacing="1"
                >A<tspan letter-spacing="3">BC</tspan>D</text>
            </svg>
        """
        )
        strings = drawing.contents[0].contents[0].contents
        assert [s.text for s in strings] == ["A", "B", "C", "D"]
        wa, wb, wc, _ = (stringWidth(c, "Helvetica", 20) for c in "ABCD")
        assert [s.x for s in strings] == pytest.approx(
            [10, 10 + wa + 1, 10 + wa + wb + 4, 10 + wa + wb + wc + 7]
        )

    def test_no_letter_spacing_keeps_single_strings(self):
        """Without letter-spacing the output is exactly as before: one String
        per fragment, positioned by cumulative bare widths."""
        drawing = drawing_from_svg(
            """
            <svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">
              <text x="10" y="50" font-size="20">AB<tspan>CD</tspan></text>
            </svg>
        """
        )
        strings = drawing.contents[0].contents[0].contents
        assert [s.text for s in strings] == ["AB", "CD"]
        assert strings[0].x == 10
        assert strings[1].x == 10 + stringWidth("AB", "Helvetica", 20)

    def test_anchor_middle_with_letter_spacing(self):
        """A centered chunk is aligned by its total width, spacing included,
        with no spacing after the last character."""
        drawing = drawing_from_svg(
            """
            <svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">
              <text x="100" y="50" font-size="20" letter-spacing="2"
                    text-anchor="middle">ABC</text>
            </svg>
        """
        )
        strings = drawing.contents[0].contents[0].contents
        total = stringWidth("ABC", "Helvetica", 20) + 2 * 2
        left, right = rendered_span(strings[0])[0], rendered_span(strings[-1])[1]
        assert left == pytest.approx(100 - total / 2)
        assert right == pytest.approx(100 + total / 2)

    def test_anchor_end_with_letter_spacing_and_tspan(self):
        """A right-aligned chunk ends at the anchor, tspans and tail text
        included; the last character carries no trailing spacing."""
        drawing = drawing_from_svg(
            """
            <svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">
              <text x="100" y="50" font-size="20" letter-spacing="2"
                    text-anchor="end">AB<tspan>CD</tspan>EF</text>
            </svg>
        """
        )
        strings = drawing.contents[0].contents[0].contents
        assert [s.text for s in strings] == list("ABCDEF")
        total = stringWidth("ABCDEF", "Helvetica", 20) + 2 * 5
        left, right = rendered_span(strings[0])[0], rendered_span(strings[-1])[1]
        assert left == pytest.approx(100 - total)
        assert right == pytest.approx(100)


class TestTextAnchorChunks:
    def test_tspans_align_as_one_chunk(self):
        """Centered and right-aligned text with tspans is aligned by the
        total width of all fragments, not fragment by fragment."""
        drawing = drawing_from_svg(
            """
            <svg xmlns="http://www.w3.org/2000/svg" width="400" height="100">
              <text x="100" y="50" font-size="20"
                    text-anchor="middle">AB<tspan>CD</tspan>EF</text>
              <text x="300" y="50" font-size="20"
                    text-anchor="end">AB<tspan>CD</tspan>EF</text>
            </svg>
        """
        )
        middle, end = drawing.contents[0].contents
        total = stringWidth("ABCDEF", "Helvetica", 20)
        left = min(rendered_span(s)[0] for s in middle.contents)
        right = max(rendered_span(s)[1] for s in middle.contents)
        assert left == pytest.approx(100 - total / 2)
        assert right == pytest.approx(100 + total / 2)
        left = min(rendered_span(s)[0] for s in end.contents)
        right = max(rendered_span(s)[1] for s in end.contents)
        assert left == pytest.approx(300 - total)
        assert right == pytest.approx(300)

    def test_tspan_with_x_starts_new_chunk(self):
        """A tspan with its own x starts a new chunk, aligned by its own
        text-anchor, while the first chunk keeps the <text> anchor."""
        drawing = drawing_from_svg(
            """
            <svg xmlns="http://www.w3.org/2000/svg" width="400" height="100">
              <text x="100" y="50" font-size="20" text-anchor="middle"
                >AB<tspan x="200" text-anchor="end">CD</tspan><tspan
                    x="300">EF</tspan></text>
            </svg>
        """
        )
        strings = drawing.contents[0].contents[0].contents
        assert [s.text for s in strings] == ["AB", "CD", "EF"]
        wab, wcd, wef = (stringWidth(t, "Helvetica", 20) for t in ("AB", "CD", "EF"))
        # First chunk centered on 100.
        assert rendered_span(strings[0]) == pytest.approx(
            (100 - wab / 2, 100 + wab / 2)
        )
        # Second chunk right-aligned on its own x, by its own anchor.
        assert rendered_span(strings[1]) == pytest.approx((200 - wcd, 200))
        # Third chunk inherits "middle" from the <text> element.
        assert rendered_span(strings[2]) == pytest.approx(
            (300 - wef / 2, 300 + wef / 2)
        )

    def test_single_fragment_anchor_is_left_to_reportlab(self):
        """A single-run text keeps its x and textAnchor untouched, so old
        documents render exactly as before."""
        drawing = drawing_from_svg(
            """
            <svg xmlns="http://www.w3.org/2000/svg" width="200" height="100">
              <text x="100" y="50" font-size="20" text-anchor="middle">ABC</text>
              <text x="100" y="80" font-size="20" text-anchor="end">DEF</text>
            </svg>
        """
        )
        middle, end = drawing.contents[0].contents
        assert middle.contents[0].x == 100
        assert middle.contents[0].textAnchor == "middle"
        assert end.contents[0].x == 100
        assert end.contents[0].textAnchor == "end"
