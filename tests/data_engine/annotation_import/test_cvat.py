import zipfile

import pytest
from dagshub_annotation_converter.ir.image import IRBBoxImageAnnotation

from dagshub.data_engine.annotation.importer import AnnotationImporter

_CVAT_IMAGE_XML = b"""<?xml version="1.0" encoding="utf-8"?>
<annotations>
  <version>1.1</version>
  <image id="0" name="img.jpg" width="100" height="50">
    <box label="cat" source="manual" occluded="0" xtl="10" ytl="5" xbr="30" ybr="25" z_order="0"></box>
  </image>
</annotations>
"""


@pytest.mark.parametrize("as_zip", [False, True])
def test_import_cvat_image_annotations(ds, tmp_path, as_zip):
    if as_zip:
        annotations_file = tmp_path / "annotations.zip"
        with zipfile.ZipFile(annotations_file, "w") as z:
            z.writestr("annotations.xml", _CVAT_IMAGE_XML)
    else:
        annotations_file = tmp_path / "annotations.xml"
        annotations_file.write_bytes(_CVAT_IMAGE_XML)

    importer = AnnotationImporter(ds, "cvat", annotations_file, load_from="disk")
    result = importer.import_annotations()

    assert list(result.keys()) == ["img.jpg"]
    assert len(result["img.jpg"]) == 1
    assert isinstance(result["img.jpg"][0], IRBBoxImageAnnotation)
