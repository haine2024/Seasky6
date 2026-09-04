"""Step 3 — Code generation.

Article take-away:
  - 单文件 HTML + 一段 JavaScript，没有框架，没有数据库。
  - 重逻辑 95% 在浏览器就能跑完。
  - 工具放最上面，废话放下面（避免 Pogo-sticking）。

This module ships hand-crafted, deterministic HTML templates for the
3 niche types that the demo targets (small_calculator, text_processor,
generator). Real production would call an LLM with structured output
and a rubric prompt, but the templates show the exact shape.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from string import Template
from typing import Optional
import re
import textwrap


@dataclass
class ToolSpec:
    """Plan: what the tool does + the inputs/outputs."""
    name: str                 # "Mortgage vs interest calculator"
    slug: str                 # "mortgage-equal-payment-vs-principal"
    niche_id: str             # "small_calculator"
    keyword: str              # primary keyword
    description: str          # 1-2 sentence intro for SEO
    inputs: list[dict] = field(default_factory=list)   # [{id,label,placeholder,type,default}]
    output: str = ""          # html element id that shows result
    template: str = "calculator"  # calculator / text_processor / generator
    extra_copy: str = ""      # bottom-of-page SEO copy


# --- helpers ---------------------------------------------------------------

def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


# --- templates -------------------------------------------------------------

PAGE_HEAD = """<!DOCTYPE html>
<html lang="$lang">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>$title</title>
<meta name="description" content="$description" />
<meta name="keywords" content="$keywords" />
<meta property="og:title" content="$title" />
<meta property="og:description" content="$description" />
<meta property="og:type" content="website" />
<link rel="canonical" href="$canonical" />
<script type="application/ld+json">
$schema
</script>
<style>
  *,*::before,*::after { box-sizing: border-box; }
  body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: #f7f7f5; color: #1a1a1a; line-height: 1.6; }
  main { max-width: 760px; margin: 0 auto; padding: 24px 16px 80px; }
  h1 { font-size: 1.6rem; font-weight: 500; margin: 0 0 12px; color: #111; }
  h2 { font-size: 1.15rem; font-weight: 500; margin: 24px 0 8px; color: #222; }
  p { margin: 0 0 12px; font-size: 0.95rem; color: #333; }
  .card { background: #ffffff; border: 1px solid #e6e4dd; border-radius: 12px; padding: 20px; margin-top: 16px; }
  .field { display: flex; flex-direction: column; margin-bottom: 12px; }
  .field label { font-size: 0.85rem; color: #444; margin-bottom: 4px; }
  .field input, .field select, .field textarea { padding: 10px 12px; border: 1px solid #d8d6cf; border-radius: 8px; font-size: 0.95rem; background: #fff; color: #111; }
  .field input:focus, .field select:focus, .field textarea:focus { outline: 2px solid #185fa5; outline-offset: 1px; }
  .actions { display: flex; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
  .btn { padding: 10px 16px; border-radius: 8px; border: 0; cursor: pointer; font-size: 0.95rem; font-weight: 500; background: #185fa5; color: #fff; }
  .btn.secondary { background: #f0eee6; color: #222; }
  .result { margin-top: 16px; padding: 16px; background: #fafaf7; border: 1px dashed #d8d6cf; border-radius: 8px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.9rem; white-space: pre-wrap; word-break: break-word; min-height: 60px; }
  footer.site { margin-top: 48px; padding-top: 24px; border-top: 1px solid #e6e4dd; font-size: 0.8rem; color: #666; display: flex; flex-wrap: wrap; gap: 12px; justify-content: space-between; }
  footer.site a { color: #185fa5; text-decoration: none; }
  @media (prefers-color-scheme: dark) {
    body { background: #15140f; color: #e8e6df; }
    .card { background: #1d1c17; border-color: #2c2a23; }
    .field input, .field select, .field textarea { background: #15140f; border-color: #2c2a23; color: #e8e6df; }
    .result { background: #1d1c17; border-color: #2c2a23; }
    .btn.secondary { background: #2c2a23; color: #e8e6df; }
    h1 { color: #f0eee6; } h2 { color: #e8e6df; } p { color: #c7c4ba; }
    footer.site { border-color: #2c2a23; color: #8c897f; }
  }
</style>
</head>
<body>
<main>
<h1>$h1</h1>
<p class="intro">$intro</p>
<div class="card">
$form
$actions
<div class="result" id="$output_id" aria-live="polite">Result will appear here.</div>
</div>
$extra_copy
<footer class="site">
  <div>© $year Tool Station. Built with the auto money agent.</div>
  <div>
    <a href="/about.html">About</a> ·
    <a href="/privacy.html">Privacy</a> ·
    <a href="/contact.html">Contact</a>
  </div>
</footer>
</main>
</body>
</html>
"""


JS_BLOCK = Template("""
<script>
(function() {
  const byId = id => document.getElementById(id);
  const fmt = (n, d) => Number(n).toLocaleString('en-US', { minimumFractionDigits: d || 2, maximumFractionDigits: d || 2 });
  function go() {
    try {
      $logic
      const out = byId('$output_id');
      out.textContent = $result_expr;
    } catch (e) {
      byId('$output_id').textContent = 'Error: ' + e.message;
    }
  }
  byId('$btn_id').addEventListener('click', go);
})();
</script>
""")


def render_form(fields: list[dict]) -> str:
    out = []
    for f in fields:
        fid = f["id"]
        label = f["label"]
        if f.get("type") == "textarea":
            out.append(
                f'<div class="field"><label for="{fid}">{label}</label>'
                f'<textarea id="{fid}" rows="{f.get("rows",6)}" placeholder="{f.get("placeholder","")}"></textarea></div>'
            )
        else:
            ph = f.get("placeholder", "")
            default = f.get("default", "")
            ft = f.get("type", "text")
            out.append(
                f'<div class="field"><label for="{fid}">{label}</label>'
                f'<input id="{fid}" type="{ft}" placeholder="{ph}" value="{default}" autocomplete="off" inputmode="decimal" /></div>'
            )
    return "\n".join(out)


def render_actions() -> str:
    return '<div class="actions">\n<button class="btn" id="runBtn" type="button">Run</button>\n<button class="btn secondary" id="clearBtn" type="button">Clear</button>\n</div>'


def build_schema(spec: ToolSpec, base_url: str) -> str:
    schema = {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": spec.name,
        "description": spec.description,
        "applicationCategory": "UtilitiesApplication",
        "operatingSystem": "Any",
        "url": f"{base_url.rstrip('/')}/{spec.slug}.html",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
    }
    import json
    return json.dumps(schema, indent=2)


# --- niche-specific JS -----------------------------------------------------

CALCULATOR_JS = Template(r"""
    const principal = parseFloat(byId('principal').value);
    const rate = parseFloat(byId('rate').value) / 100 / 12;
    const months = parseInt(byId('years').value) * 12;
    if (!(principal > 0) || !(rate > 0) || !(months > 0)) {
      throw new Error('Please fill principal, rate and years with positive numbers.');
    }
    const equal_payment = principal * (rate * Math.pow(1+rate, months)) / (Math.pow(1+rate, months) - 1);
    const equal_principal = principal / months + principal * rate;
    const total_equal_payment = equal_payment * months;
    const total_equal_principal = (principal / months) * months * (months + 1) / 2 * rate + principal;
    const interest_diff = total_equal_payment - total_equal_principal;
    $result_inner
""")

TEXT_PROCESSOR_JS = Template(r"""
    const input = byId('input').value;
    if (!input.length) { throw new Error('Please paste some text first.'); }
    const mode = byId('mode').value;
    let out = '';
    if (mode === 'lower') out = input.toLowerCase();
    else if (mode === 'upper') out = input.toUpperCase();
    else if (mode === 'title') out = input.replace(/\w\S*/g, w => w[0].toUpperCase() + w.slice(1).toLowerCase());
    else if (mode === 'sentence') out = input.toLowerCase().replace(/(^\s*\w|[.!?]\s+\w)/g, c => c.toUpperCase());
    else if (mode === 'dedupe') {
      out = Array.from(new Set(input.split(/\r?\n/))).filter(Boolean).join('\n');
    } else if (mode === 'reverse') out = input.split('').reverse().join('');
    else out = input;
    $result_inner_text
""")

_GENERATOR_JS_RAW = r"""
    const length = parseInt(byId('length').value);
    const upper = byId('upper').checked;
    const digits = byId('digits').checked;
    const symbols = byId('symbols').checked;
    if (!(length >= 4 && length <= 64)) throw new Error('Length must be between 4 and 64.');
    const sets = ['abcdefghijklmnopqrstuvwxyz'];
    if (upper) sets.push('ABCDEFGHIJKLMNOPQRSTUVWXYZ');
    if (digits) sets.push('0123456789');
    if (symbols) sets.push('!@#$%%^&*()-_=+[]{};:,.<>?/');
    const charset = sets.join('');
    let buf = [];
    const cryptoOK = window.crypto && window.crypto.getRandomValues;
    if (cryptoOK) {
      const arr = new Uint32Array(length);
      window.crypto.getRandomValues(arr);
      for (let i=0; i<length; i++) buf.push(charset[arr[i] % charset.length]);
    } else {
      for (let i=0; i<length; i++) buf.push(charset[Math.floor(Math.random() * charset.length)]);
    }
    const password = buf.join('');
    out_text_value
"""
GENERATOR_JS = Template(_GENERATOR_JS_RAW.replace('$%%', '$$'))


# --- niche constructors ----------------------------------------------------

def spec_for_mortgage_calc() -> ToolSpec:
    return ToolSpec(
        name="Equal payment vs equal principal mortgage calculator",
        slug="mortgage-equal-payment-vs-principal",
        niche_id="small_calculator",
        keyword="mortgage calculator equal principal vs equal payment",
        description=(
            "Compare equal payment (annuity) and equal principal mortgage "
            "schedules side by side. Free, no signup, mobile friendly."
        ),
        inputs=[
            {"id": "principal", "label": "Loan amount (USD)", "type": "number", "default": "300000", "placeholder": "e.g. 300000"},
            {"id": "rate",      "label": "Annual interest rate (%)", "type": "number", "default": "5.5", "placeholder": "e.g. 5.5"},
            {"id": "years",     "label": "Loan term (years)", "type": "number", "default": "30", "placeholder": "e.g. 30"},
        ],
        output="result",
        template="calculator",
        extra_copy=textwrap.dedent("""\
            <h2>How to read the result</h2>
            <p>Equal payment keeps your monthly payment the same across the
            loan term; equal principal keeps the principal portion the same
            and front-loads the interest. Use this calculator before you
            sign a mortgage to see which schedule costs less in total.</p>
            <h2>Frequently asked questions</h2>
            <p><strong>Which is cheaper?</strong> Equal principal usually
            costs less in total interest because you pay down the principal
            faster.</p>
            <p><strong>Can I switch mid-term?</strong> Most lenders allow
            extra principal payments at any time, which mimics the equal
            principal effect without changing your contract.</p>
        """),
    )


def spec_for_text_case() -> ToolSpec:
    return ToolSpec(
        name="Text case converter (lower / upper / title / sentence)",
        slug="text-case-converter",
        niche_id="text_processor",
        keyword="case converter sentence case",
        description=(
            "Convert any text to lowercase, UPPERCASE, Title Case, or "
            "Sentence case instantly in your browser. No upload, no signup."
        ),
        inputs=[
            {"id": "input", "label": "Your text", "type": "textarea", "placeholder": "Paste text here..."},
            {"id": "mode",  "label": "Convert to", "type": "text", "default": "title"},
        ],
        output="result",
        template="text_processor",
        extra_copy=textwrap.dedent("""\
            <h2>When to use which case</h2>
            <p>Use <strong>Sentence case</strong> for emails and Slack.
            <strong>Title Case</strong> for article headings.
            <strong>UPPER CASE</strong> only for acronyms.</p>
            <p>All processing happens locally in your browser — your text
            never leaves this page.</p>
        """),
    )


def spec_for_password_gen() -> ToolSpec:
    return ToolSpec(
        name="Strong password generator (browser only)",
        slug="strong-password-generator",
        niche_id="generator",
        keyword="wifi password generator strong",
        description=(
            "Generate a strong, random password with optional upper case, "
            "digits, and symbols. Uses crypto.getRandomValues when available."
        ),
        inputs=[
            {"id": "length",  "label": "Length", "type": "number", "default": "16", "placeholder": "4 to 64"},
            {"id": "upper",   "label": "Include A-Z", "type": "text", "default": "true"},
            {"id": "digits",  "label": "Include 0-9", "type": "text", "default": "true"},
            {"id": "symbols", "label": "Include symbols", "type": "text", "default": "true"},
        ],
        output="result",
        template="generator",
        extra_copy=textwrap.dedent("""\
            <h2>How to use this password</h2>
            <p>Save it in a password manager (Bitwarden, 1Password). Do not
            paste it into chat or email. Length matters more than
            characters — 16+ is recommended.</p>
        """),
    )


# --- render ---------------------------------------------------------------

def render_tool(
    spec: ToolSpec,
    base_url: str = "https://example.com",
    year: int = 2026,
) -> str:
    """Return final HTML for the tool, all logic inline."""
    form_html = render_form(spec.inputs)
    actions_html = render_actions()

    # JS logic per template
    if spec.template == "calculator":
        inner = r"""
        out = 'Equal payment monthly: $' + fmt(equal_payment) +
              '\nEqual principal month 1: $' + fmt(equal_principal) +
              '\nTotal interest (equal payment): $' + fmt(total_equal_payment - principal) +
              '\nTotal interest (equal principal): $' + fmt(total_equal_principal - principal) +
              '\nInterest saved with equal principal: $' + fmt(interest_diff);
        """
        logic_src = TEXT_PROCESSOR_JS  # placeholder; we override below
        # Build the actual logic for calculator
        js_logic = CALCULATOR_JS.substitute(result_inner=inner)
    elif spec.template == "text_processor":
        inner = "out;"
        js_logic = TEXT_PROCESSOR_JS.substitute(result_inner_text="out;")
    elif spec.template == "generator":
        js_logic = GENERATOR_JS.substitute(out_text_value="'Generated password: ' + password;")
    else:
        raise ValueError(f"unknown template {spec.template}")

    # final JS block injected at bottom of page
    final_js = JS_BLOCK.substitute(
        logic=js_logic,
        output_id=spec.output,
        btn_id="runBtn",
        result_expr="out",
    )

    page = Template(PAGE_HEAD)
    return page.substitute(
        lang="en",
        title=f"{spec.name} — Free &amp; Online",
        description=spec.description,
        keywords=spec.keyword + ", online tool, free, no signup",
        canonical=f"{base_url.rstrip('/')}/{spec.slug}.html",
        schema=build_schema(spec, base_url),
        h1=spec.name,
        intro=spec.description,
        form=form_html,
        output_id=spec.output,
        actions=actions_html,
        extra_copy=spec.extra_copy,
        year=year,
    ) + final_js


def write_tool(spec: ToolSpec, out_dir: Path, base_url: str = "https://example.com") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    html = render_tool(spec, base_url)
    p = out_dir / f"{spec.slug}.html"
    p.write_text(html, encoding="utf-8")
    return p
