# Firefox Walk With Me

The skin's emblem is a half-awake fox in front of red velvet curtains, with Douglas firs in the dark opening and an ivory/black chevron floor. Tactile fur, worn pigment and irregular edges connect the mark to the Northwest landscape and the Black Lodge.

![The fox in the Lodge](../assets/identity/fox-lodge.png)

The original transparent PNG is preserved and used as the main illustration on the [project page](https://georgefejer91.github.io/firefox-walk-with-me/). The native build embeds it into a self-contained icon wrapper and the green/brown desktop wordmark. That wrapper contains a bitmap; the separate vector edition below contains actual paths. The Owl Cave Start icon and recognizable Firefox browser icon remain separate identities.

Generated with the built-in imagegen tool on 17 October 2026. `transparent_background` was true. No reference image was supplied.

## Vector edition

[fox-lodge.svg](../assets/identity/fox-lodge.svg) translates the approved illustration into 1,907 colored spline paths on a transparent 1254 × 1254 viewBox. It preserves the irregular fox silhouette, velvet folds, green eye, firs and chevron floor. Fine painted texture is simplified into color shapes. There are no embedded bitmaps, fonts, scripts or external dependencies in the SVG.

Reproduce it with the optional, MIT-licensed [VTracer 0.6.15](https://pypi.org/project/vtracer/0.6.15/) artwork tool, installed in an isolated Python environment, then run `python3 tools/vectorize_logo.py`. This is an authoring dependency only; it is not downloaded by the skin installer or website. Pillow converts alpha to a binary mask at 128 before tracing, preventing faint edge pixels from becoming opaque flecks. The script records the exact spline, color and speckle settings and adds an accessible title, description and viewBox.

The website previews both editions and offers direct SVG/PNG downloads. The native desktop keeps the approved painterly rendering.

## Exact generation prompt

Use case: logo-brand, painterly illustrated emblem for an unofficial desktop skin named Firefox Walk With Me. Create a single atmospheric, unmistakably Twin Peaks / Black Lodge-inspired fox emblem on a truly transparent background. A natural, softly painted red fox curls asleep with one eye slightly open in front of a parting pair of heavy wine-red velvet theatre curtains; through the narrow curtain opening there is impossible blackness and two small misty Douglas fir silhouettes. Its long organic, furred tail forms a loose crescent around a small patch of the iconic broad black-and-ivory zigzag Black Lodge floor. The fox has a tiny eerie muted green glint in its otherwise natural eye. Mood: a mysterious object on an early-1990s surreal television title card, quiet rural Pacific Northwest dread, dream logic, old hand-painted theatre poster, velvet and forest rather than cyberpunk. Medium: delicate hand-painted gouache and slightly distressed vintage screenprint, softly irregular edges, tactile fur and velvet folds, restrained aged ivory, oxblood red, deep woodland green and brown-black. Composition: one compact, legible cohesive emblem, about 80% of a square canvas, centered, recognizable fox silhouette first, curtains and floor simple bold secondary shapes. No lettering; the exact project title will be typeset separately. No circle outline or geometric badge frame, no sharp polygon fox face, no robot or metal or circuit pattern, no gaming mascot, no shield, no flat corporate vector styling, no polished 3D render, no glowing neon. Do not copy any existing Firefox logo. It should feel haunted, intimate and handmade.
