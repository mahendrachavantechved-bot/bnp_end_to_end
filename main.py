# main.py
"""
Loan Processing Demo – Retail + SME
=====================================
Full Flet web/desktop app with:
  • 10,000 applicant dropdown with instant search
  • Side panel applicant details
  • Retail pipeline (FOIR, LTV, 10 agents)
  • SME pipeline (DSCR, Collateral, 10 agents)
  • Live Sarvam STT via browser microphone (JS interop)
  • Hindi / Kannada translation via Sarvam REST API
  • DSCR + LTV visual gauge charts
  • GitHub Pages compatible (static Pyodide build)

Run locally  : flet run main.py
Deploy (web) : flet build web  (then push – GitHub Actions deploys to Pages)
"""

import json
import os
import threading
from typing import Optional

import flet as ft

from retail_pipeline import RetailPipeline
from sme_pipeline import SMEPipeline
from sarvam_utils import (
    stt_from_bytes, translate_to_hindi, translate_to_kannada,
    is_key_configured, SARVAM_KEY
)

# ── Lazy gauge imports (matplotlib) ──────────────────────────────────────────
try:
    from gauges import dscr_gauge, ltv_gauge
    _GAUGES = True
except Exception:
    _GAUGES = False

# ── Load synthetic data ───────────────────────────────────────────────────────
def _load(path: str) -> list:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

RETAIL_DATA: list = _load("retail_applicants.json")
SME_DATA:    list = _load("sme_applicants.json")

# ── Singleton pipelines ───────────────────────────────────────────────────────
_retail_pl = RetailPipeline()
_sme_pl    = SMEPipeline()

# ── JS for browser microphone recording (WebM/Opus → Sarvam STT) ─────────────
_MIC_JS = """
(function() {
  if (window._fletRecording) return;

  var chunks   = [];
  var recorder = null;

  window.startMicRecording = function(durationMs) {
    chunks = [];
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(function(stream) {
        recorder = new MediaRecorder(stream);
        recorder.ondataavailable = function(e) { if (e.data.size > 0) chunks.push(e.data); };
        recorder.onstop = function() {
          var blob   = new Blob(chunks, { type: 'audio/webm' });
          var reader = new FileReader();
          reader.onloadend = function() {
            var b64 = reader.result.split(',')[1];
            window.__fletSendEvent('micDone', b64);
          };
          reader.readAsDataURL(blob);
          stream.getTracks().forEach(function(t) { t.stop(); });
        };
        recorder.start();
        setTimeout(function() { if (recorder && recorder.state !== 'inactive') recorder.stop(); }, durationMs || 8000);
        window.__fletSendEvent('micStarted', '');
      })
      .catch(function(err) {
        window.__fletSendEvent('micError', err.toString());
      });
  };

  window.stopMicRecording = function() {
    if (recorder && recorder.state !== 'inactive') recorder.stop();
  };

  window._fletRecording = true;
})();
"""


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _inr(n) -> str:
    try:
        return f"₹{float(n):,.0f}"
    except Exception:
        return str(n)


def _kv(label: str, value: str, highlight: bool = False) -> ft.Row:
    return ft.Row([
        ft.Text(f"{label}:", size=12, color="#8b949e", width=200),
        ft.Text(str(value), size=12, selectable=True, expand=True,
                weight="bold" if highlight else "normal",
                color="#f0f6fc" if highlight else "#c9d1d9"),
    ], spacing=6)


def _chip(text: str, color: str) -> ft.Container:
    return ft.Container(
        ft.Text(text, size=16, weight="bold", color=color),
        padding=ft.padding.symmetric(horizontal=18, vertical=10),
        bgcolor=ft.colors.with_opacity(0.15, color),
        border=ft.border.all(1, color),
        border_radius=8,
    )


def _section_title(text: str, icon: str = "") -> ft.Row:
    return ft.Row([
        ft.Text(f"{icon}  {text}" if icon else text,
                size=17, weight="bold", color="#58a6ff"),
    ])


def _card(content: ft.Control, padding: int = 18) -> ft.Container:
    return ft.Container(
        content=content,
        bgcolor="#161b22",
        padding=padding,
        border_radius=10,
        border=ft.border.all(1, "#30363d"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Main Flet app
# ─────────────────────────────────────────────────────────────────────────────
def main(page: ft.Page):
    page.title        = "Loan Processing Demo"
    page.theme_mode   = ft.ThemeMode.DARK
    page.bgcolor      = "#0d1117"
    page.padding      = 0
    page.window_width  = 1440
    page.window_height = 900
    page.scroll       = None

    # ── Inject mic JS once ────────────────────────────────────────────────────
    page.run_js(_MIC_JS)

    # ── Shared state ──────────────────────────────────────────────────────────
    selected_retail: list  = [None]
    selected_sme:    list  = [None]
    mic_target:      list  = [None]   # which TextField receives STT result
    mic_active:      list  = [False]

    # ── Results column ────────────────────────────────────────────────────────
    results_col = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=8, expand=True)

    def clear_results():
        results_col.controls.clear()
        page.update()

    def show_results(result: dict, mode: str):
        results_col.controls.clear()

        decision = result.get("decision", "N/A")
        color = (
            "#3fb950" if "APPROVE" in str(decision) else
            "#e3b341" if "REVIEW"  in str(decision) or "REFER" in str(decision) else
            "#f85149"
        )
        results_col.controls.append(_chip(f"▶  {decision}", color))
        results_col.controls.append(ft.Divider(height=10, color="#30363d"))

        if mode == "retail":
            metrics = [
                ("Applicant",         result.get("full_name", result.get("name", "N/A")), True),
                ("Loan Type",         result.get("loan_type", result.get("type", "N/A")), False),
                ("City",              result.get("city", "N/A"), False),
                ("Employment",        result.get("employment_type", "N/A"), False),
                ("CIBIL Score",       result.get("cibil_score", result.get("cibil", "N/A")), True),
                ("Monthly Income",    _inr(result.get("net_monthly_income", result.get("monthly_income", 0))), False),
                ("Proposed EMI",      _inr(result.get("proposed_emi", 0)), False),
                ("FOIR Pre-Loan",     f"{result.get('foir_pre_loan', 0):.1f}%", False),
                ("FOIR Post-Loan",    f"{result.get('foir_post_loan', 0):.1f}%  (max {result.get('max_allowed_foir', 50)}%)", True),
                ("FOIR Status",       result.get("foir_status", "N/A"), True),
                ("Loan Requested",    _inr(result.get("loan_amount_requested", result.get("loan_amt", 0))), False),
                ("Approved Amount",   _inr(result.get("approved_amount", 0)), True),
                ("Interest Rate",     f"{result.get('interest_rate', 'N/A')}%", False),
                ("Credit Score",      f"{result.get('final_score', 'N/A')} / 98", False),
                ("Risk Grade",        result.get("bureau_risk_grade", "N/A"), False),
                ("LTV Ratio",         f"{result.get('ltv_ratio', 0):.1f}%", False),
                ("NACH UMRN",         result.get("nach_umrn", "N/A"), False),
                ("Loan Account",      result.get("loan_account_number", "N/A"), False),
                ("Disbursement Mode", result.get("disbursement_mode", "N/A"), False),
            ]
        else:
            metrics = [
                ("Business",          result.get("name", result.get("business_name", "N/A")), True),
                ("Loan Type",         result.get("loan_type", result.get("type", "N/A")), False),
                ("City",              result.get("city", "N/A"), False),
                ("Industry",          result.get("industry", "N/A"), False),
                ("Annual Turnover",   _inr(result.get("annual_turnover", result.get("turnover", 0))), False),
                ("Promoter CIBIL",    result.get("promoter_cibil_score", result.get("cibil", "N/A")), True),
                ("DSCR",              f"{result.get('dscr', 0):.2f}  (min 1.25)", True),
                ("Current Ratio",     f"{result.get('current_ratio', 0):.2f}", False),
                ("Debt / Equity",     f"{result.get('debt_to_equity', 0):.2f}", False),
                ("Gross Margin",      f"{result.get('gross_profit_margin', 0):.1f}%", False),
                ("Financial Health",  f"{result.get('financial_health_score', 0):.1f} / 98", False),
                ("Collateral Value",  _inr(result.get("collateral_value", 0)), False),
                ("LTV Ratio",         f"{result.get('ltv_ratio', 0):.1f}%  (max {result.get('max_allowed_ltv', 70)}%)", True),
                ("Risk Score",        f"{result.get('total_score', 'N/A')} / 98", False),
                ("Risk Grade",        result.get("risk_grade", "N/A"), False),
                ("Loan Requested",    _inr(result.get("loan_amount_requested", result.get("loan_amt", 0))), False),
                ("Sanctioned Amount", _inr(result.get("sanctioned_amount", 0)), True),
                ("Interest Rate",     f"{result.get('final_interest_rate', 'N/A')}%", False),
                ("Conditions",        " | ".join(result.get("sanction_conditions", []) or ["None"]), False),
                ("NACH UMRN",         result.get("nach_umrn", "N/A"), False),
                ("Loan Account",      result.get("loan_account_number", "N/A"), False),
            ]

        for lbl, val, hl in metrics:
            results_col.controls.append(_kv(lbl, str(val), highlight=hl))

        # Gauges
        if _GAUGES:
            gauge_row = ft.Row([], spacing=12)
            try:
                if mode == "sme":
                    dscr_val = float(result.get("dscr", 1.0) or 1.0)
                    img = dscr_gauge(dscr_val)
                    if img:
                        gauge_row.controls.append(
                            ft.Image(src_base64=img, width=280, height=170,
                                     fit=ft.ImageFit.CONTAIN)
                        )
                ltv_val = float(result.get("ltv_ratio", 0) or 0)
                if ltv_val > 0:
                    img2 = ltv_gauge(ltv_val)
                    if img2:
                        gauge_row.controls.append(
                            ft.Image(src_base64=img2, width=280, height=170,
                                     fit=ft.ImageFit.CONTAIN)
                        )
            except Exception:
                pass
            if gauge_row.controls:
                results_col.controls.append(ft.Divider(height=8, color="#30363d"))
                results_col.controls.append(gauge_row)

        # Stage logs
        results_col.controls.append(ft.Divider(height=10, color="#30363d"))
        results_col.controls.append(
            ft.Text("Stage Log", size=13, weight="bold", color="#8b949e")
        )
        for log in result.get("logs", []):
            results_col.controls.append(
                ft.Text(log, size=11, color="#79c0ff",
                        font_family="monospace", selectable=True)
            )

        # Switch to results tab
        tabs_ctrl.selected_index = 1
        page.update()

    # ── Side panel ────────────────────────────────────────────────────────────
    side_col = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
    side_box = ft.Container(
        content=side_col,
        bgcolor="#161b22",
        padding=16,
        border_radius=10,
        border=ft.border.all(1, "#30363d"),
        visible=False,
        width=320,
    )

    def open_side(app: dict, is_retail: bool):
        side_col.controls.clear()
        name = app.get("name", "N/A")
        side_col.controls.append(
            ft.Text(name, size=14, weight="bold", color="#58a6ff")
        )
        side_col.controls.append(ft.Divider(height=6, color="#30363d"))

        if is_retail:
            fields = [
                ("City",       app.get("city")),
                ("Gender",     app.get("gender")),
                ("Age",        app.get("age")),
                ("PAN",        app.get("pan")),
                ("Mobile",     app.get("mobile")),
                ("Email",      app.get("email")),
                ("Employment", app.get("employment_type")),
                ("Loan Type",  app.get("loan_type", app.get("type"))),
                ("Purpose",    app.get("loan_purpose")),
                ("CIBIL",      app.get("cibil")),
                ("Income/mo",  _inr(app.get("monthly_income", 0))),
                ("Loan Amt",   _inr(app.get("loan_amt", 0))),
                ("Tenure",     f"{app.get('tenure_months', 'N/A')} months"),
                ("Exist EMI",  _inr(app.get("existing_emi", 0))),
            ]
        else:
            fields = [
                ("City",      app.get("city")),
                ("Industry",  app.get("industry")),
                ("PAN",       app.get("pan")),
                ("GSTIN",     app.get("gstin")),
                ("Mobile",    app.get("mobile")),
                ("Email",     app.get("email")),
                ("Promoter",  app.get("promoter_name")),
                ("CIBIL",     app.get("cibil")),
                ("Loan Type", app.get("loan_type", app.get("type"))),
                ("Purpose",   app.get("loan_purpose")),
                ("Turnover",  _inr(app.get("turnover", 0))),
                ("Loan Amt",  _inr(app.get("loan_amt", 0))),
                ("Vintage",   f"{app.get('vintage', 'N/A')} yrs"),
                ("Collateral", _inr(app.get("collateral", 0))),
            ]

        for lbl, val in fields:
            side_col.controls.append(_kv(lbl, str(val) if val is not None else "N/A"))

        side_col.controls.append(
            ft.TextButton("✕  Close", on_click=lambda _: close_side(),
                          style=ft.ButtonStyle(color="#f85149"))
        )
        side_box.visible = True
        page.update()

    def close_side():
        side_box.visible = False
        page.update()

    # ── Voice / STT helpers ───────────────────────────────────────────────────
    mic_status_text = ft.Text("", size=11, color="#e3b341")

    def _run_stt(b64_audio: str, target_field: ft.TextField):
        """Decode base64 → bytes → Sarvam STT → fill field."""
        import base64
        try:
            audio_bytes = base64.b64decode(b64_audio)
            result = stt_from_bytes(audio_bytes, filename="audio.webm", lang="en-IN")
            target_field.value = result
            mic_status_text.value = "✅  STT done"
        except Exception as e:
            mic_status_text.value = f"STT error: {e}"
        finally:
            mic_active[0] = False
            page.update()

    def on_page_event(e: ft.Event):
        if e.name == "micStarted":
            mic_status_text.value = "🔴  Recording…  (8 s)"
            page.update()
        elif e.name == "micDone":
            mic_status_text.value = "⏳  Processing with Sarvam…"
            page.update()
            if mic_target[0] is not None:
                threading.Thread(
                    target=_run_stt,
                    args=(e.data, mic_target[0]),
                    daemon=True,
                ).start()
        elif e.name == "micError":
            mic_status_text.value = f"Mic error: {e.data}"
            mic_active[0] = False
            page.update()

    page.on_event = on_page_event

    def mic_button(target_field: ft.TextField) -> ft.IconButton:
        def on_click(_):
            if not is_key_configured():
                mic_status_text.value = "⚠️  Set SARVAM_API_KEY in sarvam_utils.py"
                page.update()
                return
            mic_target[0]  = target_field
            mic_active[0]  = True
            mic_status_text.value = "⏳  Requesting microphone…"
            page.update()
            page.run_js("window.startMicRecording(8000);")

        return ft.IconButton(
            icon=ft.icons.MIC,
            icon_color="#58a6ff",
            tooltip="Record 8 s → Sarvam STT",
            on_click=on_click,
        )

    # ── Retail section ────────────────────────────────────────────────────────
    retail_dd_ref     = ft.Ref[ft.Dropdown]()
    retail_search_ref = ft.Ref[ft.TextField]()
    retail_name_ref   = ft.Ref[ft.TextField]()
    retail_progress   = ft.ProgressRing(visible=False, width=24, height=24, stroke_width=2)
    retail_status     = ft.Text("Ready", size=12, color="#3fb950")

    def retail_options(q: str = "") -> list:
        src = ([a for a in RETAIL_DATA if
                q in a.get("city","").lower() or
                q in a.get("name","").lower() or
                q in a.get("employment_type","").lower() or
                q in a.get("loan_type", a.get("type","")).lower() or
                q in a.get("loan_purpose","").lower()]
               if q else RETAIL_DATA)
        return [
            ft.dropdown.Option(
                key=a["id"],
                text=(f"{a['name']}  |  {a['city']}  |  "
                      f"{a.get('loan_type', a.get('type',''))}  |  "
                      f"{_inr(a.get('loan_amt',0))}  |  CIBIL {a.get('cibil','')}")
            ) for a in src[:500]
        ]

    def on_retail_search(e):
        retail_dd_ref.current.options = retail_options(
            (retail_search_ref.current.value or "").lower()
        )
        page.update()

    def on_retail_select(e):
        val = retail_dd_ref.current.value
        if not val:
            close_side(); return
        app = next((a for a in RETAIL_DATA if a["id"] == val), None)
        if app:
            selected_retail[0] = app
            open_side(app, is_retail=True)

    def process_retail(_e=None):
        app = selected_retail[0]
        if not app:
            page.show_snack_bar(ft.SnackBar(ft.Text("Select a retail applicant first")))
            return
        # Name override
        override = (retail_name_ref.current.value or "").strip()
        if override:
            app = dict(app, name=override, full_name=override)

        retail_progress.visible = True
        retail_status.value     = "Processing…"
        page.update()

        def _run():
            try:
                result = _retail_pl.run(app)
                show_results(result, "retail")
                retail_status.value = f"Done – {result.get('decision','N/A')}"
            except Exception as ex:
                retail_status.value = f"Error: {ex}"
            finally:
                retail_progress.visible = False
                page.update()

        threading.Thread(target=_run, daemon=True).start()

    # ── SME section ───────────────────────────────────────────────────────────
    sme_dd_ref     = ft.Ref[ft.Dropdown]()
    sme_search_ref = ft.Ref[ft.TextField]()
    sme_name_ref   = ft.Ref[ft.TextField]()
    sme_progress   = ft.ProgressRing(visible=False, width=24, height=24, stroke_width=2)
    sme_status     = ft.Text("Ready", size=12, color="#3fb950")

    def sme_options(q: str = "") -> list:
        src = ([a for a in SME_DATA if
                q in a.get("city","").lower() or
                q in a.get("name","").lower() or
                q in a.get("industry","").lower() or
                q in a.get("loan_type", a.get("type","")).lower() or
                q in a.get("loan_purpose","").lower()]
               if q else SME_DATA)
        return [
            ft.dropdown.Option(
                key=a["id"],
                text=(f"{a['name']}  |  {a['city']}  |  "
                      f"{a.get('industry','')}  |  "
                      f"{a.get('loan_type', a.get('type',''))}  |  "
                      f"{_inr(a.get('loan_amt',0))}")
            ) for a in src[:500]
        ]

    def on_sme_search(e):
        sme_dd_ref.current.options = sme_options(
            (sme_search_ref.current.value or "").lower()
        )
        page.update()

    def on_sme_select(e):
        val = sme_dd_ref.current.value
        if not val:
            close_side(); return
        app = next((a for a in SME_DATA if a["id"] == val), None)
        if app:
            selected_sme[0] = app
            open_side(app, is_retail=False)

    def process_sme(_e=None):
        app = selected_sme[0]
        if not app:
            page.show_snack_bar(ft.SnackBar(ft.Text("Select an SME applicant first")))
            return
        override = (sme_name_ref.current.value or "").strip()
        if override:
            app = dict(app, name=override, business_name=override)

        sme_progress.visible = True
        sme_status.value     = "Processing…"
        page.update()

        def _run():
            try:
                result = _sme_pl.run(app)
                show_results(result, "sme")
                sme_status.value = f"Done – {result.get('decision','N/A')}"
            except Exception as ex:
                sme_status.value = f"Error: {ex}"
            finally:
                sme_progress.visible = False
                page.update()

        threading.Thread(target=_run, daemon=True).start()

    # ── Translation actions ───────────────────────────────────────────────────
    def _translate(lang_fn, label: str):
        text_parts = []
        for ctrl in results_col.controls:
            if isinstance(ctrl, ft.Row):
                for c in ctrl.controls:
                    if isinstance(c, ft.Text) and c.value:
                        text_parts.append(c.value)
        if not text_parts:
            page.show_snack_bar(ft.SnackBar(ft.Text("Run a pipeline first")))
            return
        raw = " | ".join(text_parts[:40])[:1200]

        def _do():
            translated = lang_fn(raw)
            results_col.controls.append(ft.Divider(color="#30363d"))
            results_col.controls.append(
                _card(ft.Column([
                    ft.Text(label, size=14, weight="bold", color="#e3b341"),
                    ft.Text(translated, size=13, selectable=True, color="#f0f6fc"),
                ]), padding=14)
            )
            page.update()

        threading.Thread(target=_do, daemon=True).start()

    # ── Sarvam key status badge ───────────────────────────────────────────────
    key_ok = is_key_configured()
    key_badge = ft.Container(
        ft.Text(
            "🟢  Sarvam Voice LIVE" if key_ok else "🟡  Sarvam Voice: add API key",
            size=12,
            color="#3fb950" if key_ok else "#e3b341",
        ),
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        bgcolor=ft.colors.with_opacity(0.1, "#3fb950" if key_ok else "#e3b341"),
        border_radius=6,
        border=ft.border.all(1, "#3fb950" if key_ok else "#e3b341"),
    )

    # ── Build retail card ─────────────────────────────────────────────────────
    retail_name_field = ft.TextField(
        ref=retail_name_ref,
        label="Override / speak applicant name",
        hint_text="Leave blank to use selected name",
        border_color="#30363d",
        focused_border_color="#58a6ff",
        text_size=13,
    )

    retail_card = _card(ft.Column([
        _section_title("Retail Loan Applicants", "🏦"),
        ft.Text(f"{len(RETAIL_DATA):,} applicants loaded", size=11, color="#8b949e"),
        ft.TextField(
            ref=retail_search_ref,
            label="🔍  Search  name / city / loan type / purpose",
            on_change=on_retail_search,
            border_color="#30363d",
            focused_border_color="#58a6ff",
            text_size=13,
        ),
        ft.Dropdown(
            ref=retail_dd_ref,
            label="Select applicant",
            options=retail_options(),
            on_change=on_retail_select,
            bgcolor="#0d1117",
            text_size=12,
        ),
        retail_name_field,
        ft.Row([
            mic_button(retail_name_field),
            mic_status_text,
        ], spacing=8),
        ft.Row([
            ft.ElevatedButton(
                "▶  Process Retail",
                on_click=process_retail,
                icon=ft.icons.PLAY_CIRCLE_FILLED_ROUNDED,
                bgcolor="#1f6feb",
                color="white",
                height=42,
            ),
            retail_progress,
            retail_status,
        ], spacing=12),
    ], spacing=12))

    # ── Build SME card ────────────────────────────────────────────────────────
    sme_name_field = ft.TextField(
        ref=sme_name_ref,
        label="Override / speak business name",
        hint_text="Leave blank to use selected name",
        border_color="#30363d",
        focused_border_color="#f0883e",
        text_size=13,
    )

    sme_card = _card(ft.Column([
        _section_title("SME / Corporate Trade Finance", "🏭"),
        ft.Text(f"{len(SME_DATA):,} applicants loaded", size=11, color="#8b949e"),
        ft.TextField(
            ref=sme_search_ref,
            label="🔍  Search  name / city / industry / loan type",
            on_change=on_sme_search,
            border_color="#30363d",
            focused_border_color="#f0883e",
            text_size=13,
        ),
        ft.Dropdown(
            ref=sme_dd_ref,
            label="Select business",
            options=sme_options(),
            on_change=on_sme_select,
            bgcolor="#0d1117",
            text_size=12,
        ),
        sme_name_field,
        ft.Row([
            mic_button(sme_name_field),
            ft.Text("Mic → Sarvam STT", size=11, color="#8b949e"),
        ], spacing=8),
        ft.Row([
            ft.ElevatedButton(
                "▶  Process SME",
                on_click=process_sme,
                icon=ft.icons.PLAY_CIRCLE_FILLED_ROUNDED,
                bgcolor="#b08800",
                color="white",
                height=42,
            ),
            sme_progress,
            sme_status,
        ], spacing=12),
    ], spacing=12))

    # ── Applications tab layout ───────────────────────────────────────────────
    left_col = ft.Column(
        [retail_card, sme_card],
        spacing=16,
        expand=2,
        scroll=ft.ScrollMode.AUTO,
    )

    apps_tab_content = ft.Row(
        [left_col, side_box],
        spacing=14,
        expand=True,
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    # ── Results tab layout ────────────────────────────────────────────────────
    results_tab_content = ft.Column([
        ft.Container(
            content=results_col,
            expand=True,
            bgcolor="#161b22",
            padding=16,
            border_radius=10,
            border=ft.border.all(1, "#30363d"),
        ),
        ft.Row([
            ft.ElevatedButton(
                "🌐  Hindi",
                on_click=lambda _: _translate(translate_to_hindi, "हिंदी अनुवाद"),
                bgcolor="#21262d",
                height=38,
            ),
            ft.ElevatedButton(
                "🌐  Kannada",
                on_click=lambda _: _translate(translate_to_kannada, "ಕನ್ನಡ ಅನುವಾದ"),
                bgcolor="#21262d",
                height=38,
            ),
            ft.ElevatedButton(
                "🗑  Clear",
                on_click=lambda _: clear_results(),
                bgcolor="#21262d",
                height=38,
            ),
        ], spacing=10),
    ], expand=True, spacing=10)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tabs_ctrl = ft.Tabs(
        selected_index=0,
        animation_duration=180,
        expand=True,
        tabs=[
            ft.Tab(text="  Applications  ", content=apps_tab_content),
            ft.Tab(text="  Results  ",      content=results_tab_content),
        ],
    )

    # ── Header ────────────────────────────────────────────────────────────────
    header = ft.Container(
        ft.Row([
            ft.Text("  Loan Processing Demo", size=22, weight="bold", color="#58a6ff"),
            ft.Row([
                ft.Text("Retail + SME  |  10,000 applicants  |  Sarvam Voice",
                        size=12, color="#8b949e"),
                key_badge,
            ], spacing=14),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        bgcolor="#161b22",
        padding=ft.padding.symmetric(horizontal=28, vertical=12),
        border=ft.border.only(bottom=ft.border.BorderSide(1, "#30363d")),
    )

    page.add(ft.Column([
        header,
        ft.Container(content=tabs_ctrl, expand=True, padding=16),
    ], spacing=0, expand=True))
    page.update()


ft.app(target=main)
