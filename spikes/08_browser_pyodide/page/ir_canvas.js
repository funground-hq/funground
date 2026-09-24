// Spike 08, Part 2: a pure-JavaScript consumer of Playground's IR JSON
// (the format of tests/snapshots/*.json == Frame.to_jsonable()) drawing with
// the Canvas 2D API. Mirrors playground/renderers/cairo2d.py op for op.
//
// Text is the one deliberate deviation: it uses ctx.fillText with the bundled
// DejaVu Sans loaded as a FontFace (browser shaping), NOT the deterministic
// fontTools outline route the desktop renderer uses. See index.html.

// Every snapshot is a 640x400 sketch except 12_default_window (Sketch default 640x480).
export const SNAPSHOTS = {
  "01_first_sketch": [640, 400],
  "02_shapes": [640, 400],
  "03_colors": [640, 400],
  "04_fill_stroke": [640, 400],
  "05_text": [640, 400],
  "06_animation": [640, 400],
  "07_bounce": [640, 400],
  "08_mouse": [640, 400],
  "09_keyboard": [640, 400],
  "10_helpers": [640, 400],
  "12_default_window": [640, 480],
};

// DejaVu Sans metrics (font units); baseline = y + ascent * size / upem, as in
// playground/typography.py (contract T1: (x, y) is the top-left of the em box).
export const FONT = { family: "Playground DejaVu Sans", upem: 2048, ascent: 1901 };

export async function loadFont(url) {
  const face = new FontFace(FONT.family, `url(${url})`);
  await face.load();
  document.fonts.add(face);
  return face;
}

export const rgba = (c) => `rgba(${c[0]},${c[1]},${c[2]},${c[3] / 255})`;

function tracePath(ctx, segs) {
  ctx.beginPath();
  for (const s of segs) {
    switch (s[0]) {
      case "move": ctx.moveTo(s[1][0], s[1][1]); break;
      case "line": ctx.lineTo(s[1][0], s[1][1]); break;
      case "cubic": ctx.bezierCurveTo(s[1][0], s[1][1], s[2][0], s[2][1], s[3][0], s[3][1]); break;
      case "quad": ctx.quadraticCurveTo(s[1][0], s[1][1], s[2][0], s[2][1]); break;
      case "close": ctx.closePath(); break;
      default: throw new Error(`unknown path segment ${s[0]}`);
    }
  }
}

// Fill first, stroke on top (contract S5); strokes centred, round joins/caps (S4, D-004).
function paint(ctx, style) {
  if (style.fill) { ctx.fillStyle = rgba(style.fill); ctx.fill(); }
  if (style.stroke) { ctx.strokeStyle = rgba(style.stroke); ctx.lineWidth = style.stroke_width; ctx.stroke(); }
}

/**
 * Draw one IR frame (a list of op dicts) onto a 2D context whose user space is
 * logical pixels. Returns the number of Canvas 2D calls made (roughly).
 */
export function drawFrame(ctx, ops, width, height) {
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  let depth = 0, calls = 0;
  for (const op of ops) {
    switch (op.op) {
      case "Clear":
        // Cairo: save, reset_clip, OPERATOR_SOURCE paint, restore. Canvas cannot drop the
        // clip without restoring, so Clear inside a clip stays clipped (no snapshot does this).
        ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.scale(ctx._dpr || 1, ctx._dpr || 1);
        ctx.globalCompositeOperation = "copy"; ctx.fillStyle = rgba(op.color);
        ctx.fillRect(0, 0, width, height); ctx.restore(); calls += 6; break;
      case "Save": ctx.save(); depth++; calls++; break;
      case "Restore":
        if (depth === 0) throw new Error("Restore without Save in frame");
        ctx.restore(); depth--; calls++; break;
      case "Concat": { const [a, b, c, d, e, f] = op.transform; ctx.transform(a, b, c, d, e, f); calls++; break; }
      case "ClipPath": tracePath(ctx, op.path); ctx.clip(); calls += 2 + op.path.length; break;
      case "FillPath": tracePath(ctx, op.path); ctx.fillStyle = rgba(op.color); ctx.fill(); calls += 3 + op.path.length; break;
      case "StrokePath":
        tracePath(ctx, op.path); ctx.strokeStyle = rgba(op.color); ctx.lineWidth = op.width; ctx.stroke();
        calls += 4 + op.path.length; break;
      case "Circle":
        ctx.beginPath(); ctx.arc(op.x, op.y, Math.max(0, op.diameter / 2), 0, 2 * Math.PI);
        paint(ctx, op.style); calls += 7; break;
      case "Ellipse":
        ctx.beginPath();
        if (op.width > 0 && op.height > 0) ctx.ellipse(op.x, op.y, op.width / 2, op.height / 2, 0, 0, 2 * Math.PI);
        paint(ctx, op.style); calls += 7; break;
      case "Rect":
        ctx.beginPath(); ctx.rect(op.x, op.y, op.width, op.height); paint(ctx, op.style); calls += 7; break;
      case "Line":
        if (op.style.stroke) {
          ctx.beginPath(); ctx.moveTo(op.x1, op.y1); ctx.lineTo(op.x2, op.y2);
          ctx.strokeStyle = rgba(op.style.stroke); ctx.lineWidth = op.style.stroke_width; ctx.stroke(); calls += 6;
        }
        break;
      case "Point":
        if (op.style.stroke) {                      // a dot of diameter ~ stroke_width (S7)
          ctx.beginPath(); ctx.arc(op.x, op.y, Math.max(0.5, op.style.stroke_width / 2), 0, 2 * Math.PI);
          ctx.fillStyle = rgba(op.style.stroke); ctx.fill(); calls += 4;
        }
        break;
      case "Text": {                                // browser-native text, NOT the outline route
        const size = op.style.text_size;
        ctx.font = `${size}px "${FONT.family}"`;
        ctx.textBaseline = "alphabetic";
        ctx.textAlign = "left";
        ctx.fillStyle = rgba(op.color);
        ctx.fillText(String(op.text), op.x, op.y + FONT.ascent * size / FONT.upem);
        calls += 5; break;
      }
      default: throw new Error(`IR op ${op.op} is not implemented by ir_canvas.js`);
    }
  }
  while (depth) { ctx.restore(); depth--; }       // an unbalanced frame must not leak state
  return calls;
}

/** Size a canvas for logical (width, height) at the device pixel ratio (contract C3). */
export function prepareCanvas(canvas, width, height, dpr = window.devicePixelRatio || 1) {
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx._dpr = dpr;
  return ctx;
}
