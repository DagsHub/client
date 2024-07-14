import pytest

from dagshub.data_engine.annotation.importer import AnnotationImporter, CannotRemapPathError


@pytest.mark.parametrize(
    "in_path, expected",
    [
        ("images/1.png", "data/images/1.png"),
        ("images/2.png", "data/images/2.png"),
        ("3.png", "data/3.png"),
        ("very/long/subpath/4.png", "data/very/long/subpath/4.png"),
    ],
)
def test_dp_path_is_longer(in_path, expected):
    ann_path = "images/1.png"
    dp_path = "data/images/1.png"

    remap_func = AnnotationImporter.generate_path_map_func(ann_path, dp_path)

    actual = remap_func(in_path)
    assert actual == expected


@pytest.mark.parametrize(
    "in_path, expected",
    [
        ("data/images/1.png", "images/1.png"),
        ("data/images/2.png", "images/2.png"),
        ("data/3.png", "3.png"),
        ("data/very/long/subpath/4.png", "very/long/subpath/4.png"),
        ("5.png", None),
    ],
)
def test_dp_path_is_shorter(in_path, expected):
    ann_path = "data/images/1.png"
    dp_path = "images/1.png"

    remap_func = AnnotationImporter.generate_path_map_func(ann_path, dp_path)

    actual = remap_func(in_path)
    assert actual == expected


@pytest.mark.parametrize(
    "dp_path",
    [
        "data/different_prefix/1.png",
        "data/images/more/1.png",
        "data/more/images/1.png",
        "different_prefix/images/1.png",  # This case has too many edge cases, so we also don't handle this
    ],
)
def test_different_paths_throw_errors(dp_path):
    ann_path = "data/images/1.png"

    with pytest.raises(CannotRemapPathError):
        AnnotationImporter.generate_path_map_func(ann_path, dp_path)


def test_multiple_dp_matching():
    ann_path = "images/blabla/1.png"
    candidates = [
        "images/1.png",
        "data/images/1.png",
        "data/images/blabla/1.png",
        "images/blabla/blabla/1.png",
        "images/random/1.png",
    ]

    expected = "data/images/blabla/1.png"
    actual = AnnotationImporter.get_best_fit_datapoint_path(ann_path, candidates)

    assert actual == expected
