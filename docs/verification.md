# Verification record

16 October 2026 · MX Linux · XFCE 4.20 · X11

| Check | Result | Evidence / limit |
| --- | --- | --- |
| Native build | VERIFIED | `python3 tools/build.py` builds GTK, XFWM, SVG aliases, Xcursor files and panel images. |
| GTK3 / GTK4 CSS | VERIFIED | Native parsers report no errors for the built styles. Legacy GTK3 properties are removed from GTK4's compatibility copy. |
| Icons | VERIFIED | Native Gtk.IconTheme loads representative aliases at 16/24/48/96 pixels. Five special-folder targets resolve to five distinct SVGs. |
| Cursors | VERIFIED | libXcursor loads all aliases at 24/32/48/64 pixels; dimensions and hotspots are in bounds. |
| Audio file | VERIFIED | Stereo, 48 kHz, 6.4 seconds; peak at or below −6 dBFS; zero endpoints. |
| Rollback | VERIFIED | Temporary-filesystem tests preserve originals, symlinks, absent files, repeated installs, and typed XFConf values. XML patching preserves unrelated settings. |
| Live desktop | VERIFIED | Repeated captures and visual inspection of panel, Start menu and Thunar on the target 2× desktop. Personal application captures stay outside Git. |
| Clean-session screens | VERIFIED | Native XFCE in disposable X11 sessions, synthetic folders/text, at 1× and 2×. Reviewed desktop, Start menu, files, selection, dialog and terminal. |
| New-user defaults | VERIFIED | Clean-session first-login initialization selects the actual monitor wallpaper and matching window/panel scale. System and skel settings installed with rollback. |
| LightDM configuration | PARTIAL | Background, theme, icons, cursor and font configured. No live greeter authentication/session restart was performed. |
| GTK2 application rendering | PARTIAL | Native source is shipped; a GTK2 application screenshot is not part of this review. |
| Startup playback after login | NOT RUN | Autostart entry enabled on the target desktop; file and playback transport checked. No logout, reboot, firmware or driver change was used. Speaker audibility is not established by a muted transport check. |
| Power/stability settings | VERIFIED | XFCE idle-suspend values remain 0 for AC and battery. No power test, thermal change or audio-driver installation. |

## Screenshot-led corrections

- Initial panel had disconnected bevels, pseudo-handles and app substitutions that concealed recognizable logos.
- Removed the legacy panel rules and used one velvet surface with stable hover/active geometry.
- A screenshot caught an SVG namespace format-sniffing failure on Start; serialization now uses a conventional SVG root, checked by Gtk.IconTheme.
- A screenshot caught plugin-to-plugin pattern seams. XFCE's image background mode now aligns the shared image by plugin geometry, at each display scale.
- Reduced the icon sizes consistently and forced the tray into one row.
- Clean-session screenshots caught a missing first-login wallpaper on a differently named monitor; initialization now targets the actual monitor.
- Checked inactive file selection and dialog legibility as separate states.

Public screenshots combine a reviewed live desktop/panel capture with native test-session captures containing generic content. The full private capture history and rollback backups are intentionally excluded. Re-run `tools/preview.py` after visual changes; do not claim universal visual perfection from a finite review.

## Branding update — 17 October 2026

VERIFIED: Firefox Walk With Me naming, painterly transparent fox artwork, self-contained icon wrapper and desktop wordmark. The new mark loads through Gtk.IconTheme at 16/24/48/96 pixels, with a distinct target from the Owl Cave Start icon. Both 1× and 2× native preview sessions were captured again. Source PNG alpha spans 0–255 and is preserved. Existing installation IDs and rollback journals are reused. Live power settings remain 0 on AC and battery.

## Website and vector edition — 19 October 2026

| Check | Result | Evidence / limit |
| --- | --- | --- |
| True vector emblem | VERIFIED | 1,907 spline paths, 1254 × 1254 viewBox, accessible title/description, no embedded bitmap or external resource. Native librsvg render retains transparent corners and an opaque subject. The original PNG is unchanged. |
| Vector appearance | VERIFIED | Rendered and compared with the approved PNG. Organic silhouette, curtains, firs, green eye and chevron floor remain; fine painted texture becomes solid color shapes. Binary alpha preprocessing removes faint edge flecks. |
| Local web links | VERIFIED | Local assets and anchor targets resolve; SVG and PNG download links point to the shipped artwork. |
| Browser rendering | VERIFIED | Isolated Chrome 155 at 1440 × 1000, 768 × 1024, 390 × 844 and 320 × 740. All images decode, no horizontal page overflow, no JavaScript exceptions or failed resource requests. Primary controls have at least 40px height. |
| Screenshot review | VERIFIED | Desktop and phone screenshots inspected. Increased green-title contrast and moved the fox higher on phones. Native desktop, file-manager and terminal images are existing reviewed captures with generic content. |
| Native regression checks | VERIFIED | Rebuilt the skin; GTK3/4 parsing, representative icon/cursor loading, audio-file checks and all three installer/rollback tests pass. No installation or system-setting change was needed for this update. |
| Other web browsers / screen readers | NOT RUN | Native semantics, alt text, visible keyboard focus and a skip link are provided; independent browser and assistive-technology qualification remains open. |

The website is static HTML/CSS, with no analytics, cookies, external fonts or application JavaScript. Browser QA used an isolated temporary Chrome profile; no private application screenshots are published.
