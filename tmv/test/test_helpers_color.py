import pytest
from helpers.color import hex_to_rgb


def test_GivenRegularHexCode_ConvertsToCorrectRGBValue():
    pairs = [
        ("#FFFFFF", (255, 255, 255)),
        ("#ff00aa", (255, 0, 170)),
        ("#000000", (0, 0, 0)),
    ]

    for (hexVal, rgbVal) in pairs:
        assert hex_to_rgb(hexVal) == rgbVal


def test_GivenShortHexCode_ConvertsToCorrectRGBValue():
    pairs = [("#fff", (255, 255, 255)), ("#f0a", (255, 0, 170)), ("#000", (0, 0, 0))]

    for (hexVal, rgbVal) in pairs:
        assert hex_to_rgb(hexVal) == rgbVal


def test_GivenHexCodeWithoutHashmark_ConvertsToCorrectRGBValue():
    pairs = [
        ("FFFFFF", (255, 255, 255)),
        ("ff00aa", (255, 0, 170)),
        ("000000", (0, 0, 0)),
    ]

    for (hexVal, rgbVal) in pairs:
        assert hex_to_rgb(hexVal) == rgbVal


def test_GivenWrongFormat_RaisesError():
    with pytest.raises(ValueError):
        hex_to_rgb("hello")
