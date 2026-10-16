# Visual direction and research

Reviewed 16 October 2026. This is an unofficial fan-inspired desktop skin.

The native interface combines oxblood velvet, ivory/black chevrons, green lettering, brown title interiors, square controls, and quiet content areas. The controls retain XFCE behavior. Familiar apps retain their recognizable silhouettes.

| Reference | Evidence | Design decision |
| --- | --- | --- |
| [Richard Hoover interview](https://splendoid.net/filminutiae/interview-richard-hoover-production-designer-twin-peaks-1990) | The production designer describes Lynch's Red Room, hung drapery and a painted floor, alongside the ordinary Northwest locations. | Use folds and flooring in the desktop and interface chrome; keep file content calm. |
| [Art of the Title: Twin Peaks](https://www.artofthetitle.com/title/twin-peaks/) | The 1990 opening sequence combines industry, landscape and green-outlined brown lettering. | An outlined green/umber identity and restrained green labels connect the opening to the Red Room. |
| [AIGA Eye on Design: Lynch's typography](https://eyeondesign.aiga.org/normality-tinged-with-perversion-david-lynchs-use-of-typography/) | Describes the opening's brown/green palette; the exact font identification is qualified. | Use installed URW Gothic as an open approximation. No proprietary title font is distributed. |
| [Oventype title reference](https://oventype.com/inuse/twin-peaks-opening-titles/) | Identifies the condensed Avant Garde treatment and Pacific Title credit. | Favor geometric uppercase identity lettering, without claiming an exact font reproduction. |

The first three are the strongest complementary references: set construction, the sequence itself, and typography analysis. The desktop palette and placement rules are our interpretation. No source photograph, show frame, recording, or transcribed theme melody is included.

## Native implementation references

- [XFCE panel theming](https://docs.xfce.org/xfce/xfce4-panel/theming) documents the panel/plugin selectors.
- [XFCE 4.20 plugin background alignment](https://github.com/xfce-mirror/xfce4-panel/blob/xfce-4.20/wrapper/wrapper-plug-x11.c) offsets an image according to plugin geometry. The shared panel image uses this mechanism to continue the chevrons and folds through separate plugin windows.
- [Thunar icon renderer](https://github.com/xfce-mirror/thunar/blob/master/thunar/thunar-icon-renderer.c) explains selection tinting. Inactive selection must remain readable in a dark theme.

## Review criteria

1. Panel texture joins across Start, dock, tray and clock; no fake handles or competing bevels.
2. Hover and active outlines do not move the icons or alter the bar height.
3. The Owl Cave mark identifies Start. The owl is secondary, including the default avatar/category artwork.
4. Firefox, Chrome and other available Papirus app silhouettes remain recognizable. The optional ChatGPT composition keeps the official white knot geometry over velvet.
5. Documents, Pictures, Downloads, Music and Videos have different shapes. Filenames, selections, dialogs and terminal text remain legible.
6. Pattern is concentrated in chrome and desktop surroundings; document surfaces remain dark and still.

This review covers the shipped surfaces, not every third-party application or future app update. Apps with their own drawn controls or tray artwork can retain their own styling.
