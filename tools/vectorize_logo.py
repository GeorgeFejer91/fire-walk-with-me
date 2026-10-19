#!/usr/bin/env python3
"""Optional artwork tool; the skin and site do not require VTracer to run."""
from importlib.metadata import version
from pathlib import Path
from xml.etree import ElementTree as ET

import vtracer
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SVG = 'http://www.w3.org/2000/svg'


def main():
    if version('vtracer') != '0.6.15':
        raise SystemExit('Use vtracer==0.6.15 to reproduce the published graphic.')
    output = ROOT / 'assets/identity/fox-lodge.svg'
    with Image.open(ROOT / 'assets/identity/fox-lodge.png') as image:
        rgba = image.convert('RGBA')
    # VTracer uses binary alpha; discard faint edge noise before tracing it.
    pixels = [(r, g, b, 255 if a >= 128 else 0) for r, g, b, a in rgba.getdata()]
    graphic = vtracer.convert_pixels_to_svg(
        pixels, rgba.size,
        colormode='color', hierarchical='stacked', mode='spline',
        filter_speckle=8, color_precision=5, layer_difference=24,
        corner_threshold=60, length_threshold=4.0, max_iterations=10,
        splice_threshold=45, path_precision=2,
    )
    output.write_text(graphic)
    tree = ET.parse(output)
    root = tree.getroot()
    root.set('viewBox', '0 0 1254 1254')
    root.set('role', 'img')
    root.set('aria-labelledby', 'title description')
    title = ET.Element(f'{{{SVG}}}title', id='title')
    title.text = 'Firefox Walk With Me — the fox in the Lodge'
    description = ET.Element(f'{{{SVG}}}desc', id='description')
    description.text = ('A curled red fox with a green eye, velvet curtains, '
                        'dark fir trees and an ivory-and-black chevron floor. '
                        'A path-based vector edition of the painterly emblem.')
    root.insert(0, title)
    root.insert(1, description)
    ET.register_namespace('', SVG)
    tree.write(output, encoding='utf-8', xml_declaration=True)
    paths = list(root.iter(f'{{{SVG}}}path'))
    assert paths and not list(root.iter(f'{{{SVG}}}image'))
    assert all(element.tag in {f'{{{SVG}}}{tag}' for tag in
               ('svg', 'title', 'desc', 'path')} for element in root.iter())
    print(f'{output.name}: {len(paths)} paths, {output.stat().st_size:,} bytes')


if __name__ == '__main__':
    main()
