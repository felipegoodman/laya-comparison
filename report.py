#!/usr/bin/env python3
"""Corre Falcon3 y Laya sobre cases/ y escribe report.html.

Precisión de un caso: 100 si el área y requiere_revision coinciden con
ESPERADO, 0 si no. Precisión general: aciertos / casos. Precisión por
área: veces que acertó esa área / veces que la eligió.

Tiempo de caso: solo la clasificación. Tiempo general: carga del modelo
más la suma de los casos.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from laya import Router

import classifier
from llm_classifier import AREAS, CASES_DIR, MANUAL, classify as classify_falcon
from llm_classifier import evaluate, load_cases

ROOT = Path(__file__).resolve().parent
REPORT_PATH = ROOT / "report.html"

FALCON = "Falcon3"
LAYA = "Laya"


def _row(case, data: dict | None, seconds: float, error: str | None) -> dict:
    if data is None:
        scored = {
            "area": None,
            "area_ok": False,
            "revision_ok": False,
            "ok": False,
        }
    else:
        scored = evaluate(case, data)
    ok = bool(scored["ok"])
    return {
        "caso": Path(case.name).stem,
        "esperado": case.expected_area,
        "area": scored["area"],
        "area_ok": scored["area_ok"],
        "revision_ok": scored["revision_ok"],
        "ok": ok,
        "precision": 100.0 if ok else 0.0,
        "segundos": round(seconds, 2),
        "error": error,
    }


def _precision_por_area(rows: list[dict]) -> list[dict]:
    stats = []
    for area in AREAS:
        chosen = [row for row in rows if row["area"] == area]
        hits = sum(1 for row in chosen if row["esperado"] == area)
        precision = None if not chosen else round(100.0 * hits / len(chosen), 1)
        stats.append(
            {
                "area": area,
                "precision": precision,
                "elegida": len(chosen),
                "aciertos": hits,
            }
        )
    return stats


def _summary(name: str, rows: list[dict], carga_s: float) -> dict:
    hits = sum(1 for row in rows if row["ok"])
    total = len(rows)
    inferencia = round(sum(row["segundos"] for row in rows), 2)
    carga = round(carga_s, 2)
    return {
        "nombre": name,
        "casos": rows,
        "aciertos": hits,
        "total": total,
        "precision": round(100.0 * hits / total, 1) if total else 0.0,
        "inferencia_s": inferencia,
        "carga_s": carga,
        "general_s": round(inferencia + carga, 2),
        "por_area": _precision_por_area(rows),
    }


def run_falcon(cases, model: str) -> dict:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise SystemExit(
            "Falta openai en este entorno. Con el venv activo: pip install openai"
        ) from exc

    started = time.perf_counter()
    client = OpenAI(base_url="http://127.0.0.1:11434/v1", api_key="ollama", timeout=180)
    carga = time.perf_counter() - started
    rows = []
    for case in cases:
        started = time.perf_counter()
        error = None
        data = None
        try:
            data = classify_falcon(client, model, case)
        except Exception as exc:
            error = str(exc)
        seconds = time.perf_counter() - started
        row = _row(case, data, seconds, error)
        rows.append(row)
        mark = "ok" if row["ok"] else "fallo"
        print(f"{FALCON} {row['caso']}: {row['segundos']:.2f}s {mark}", flush=True)
    return _summary(FALCON, rows, carga)


def run_laya(cases, lang: str) -> dict:
    started = time.perf_counter()
    router = Router()
    router.load("multilingual")
    carga = time.perf_counter() - started
    print(f"{LAYA} carga: {carga:.2f}s", flush=True)
    rows = []
    for case in cases:
        started = time.perf_counter()
        error = None
        data = None
        try:
            data, _routing = classifier.classify(router, case, lang)
        except Exception as exc:
            error = str(exc)
        seconds = time.perf_counter() - started
        row = _row(case, data, seconds, error)
        rows.append(row)
        mark = "ok" if row["ok"] else "fallo"
        print(f"{LAYA} {row['caso']}: {row['segundos']:.2f}s {mark}", flush=True)
    return _summary(LAYA, rows, carga)


def write_report(payload: dict, path: Path) -> None:
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    path.write_text(HTML.replace("/*__DATA__*/", data), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Informe de precisión y tiempo.")
    parser.add_argument("--cases", type=Path, default=CASES_DIR)
    parser.add_argument("--only", help="un solo caso: nombre de fichero o stem")
    parser.add_argument("--model", default="falcon3:7b")
    parser.add_argument("--lang", default="es")
    parser.add_argument("--out", type=Path, default=REPORT_PATH)
    args = parser.parse_args()

    cases = load_cases(args.cases, args.only)
    falcon = run_falcon(cases, args.model)
    laya = run_laya(cases, args.lang)
    payload = {"modelos": [falcon, laya], "areas": list(AREAS), "manual": MANUAL}
    write_report(payload, args.out)
    print(f"informe: {args.out}")
    for model in payload["modelos"]:
        print(
            f"{model['nombre']}: precisión {model['precision']}% "
            f"({model['aciertos']}/{model['total']}), "
            f"tiempo general {model['general_s']}s"
        )


HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Precisión y tiempo</title>
  <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
  <style>
    :root { color-scheme: dark; }
    body { margin: 0; font-family: "Segoe UI", sans-serif; background: #12161c; color: #e8eef6; }
    main { max-width: 1100px; margin: 0 auto; padding: 28px 20px 48px; }
    h1 { font-size: 1.4rem; font-weight: 650; margin: 0 0 6px; }
    p.note { margin: 0 0 20px; color: #9aabbd; font-size: 0.92rem; }
    .cards { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px; }
    .card, .panel { background: #1c2430; border-radius: 12px; padding: 16px 18px; }
    .card h2 { margin: 0; font-size: 1rem; }
    .card .num { font-size: 1.8rem; margin: 8px 0 0; }
    .card .sub { color: #9aabbd; font-size: 0.85rem; }
    .panel { margin-top: 12px; }
    .panel h2 { margin: 0 0 8px; font-size: 1rem; font-weight: 600; }
    table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    th, td { text-align: left; padding: 7px 8px; border-bottom: 1px solid #2c3848; }
    th { color: #9aabbd; font-weight: 600; }
    .ok { color: #3ddc97; }
    .bad { color: #f07178; }
  </style>
</head>
<body>
<main>
  <h1>Precisión y tiempo</h1>
  <p class="note">Precisión de un caso: área y revisión correctas. Precisión general: aciertos / casos. Precisión por área: aciertos de esa área / veces que el modelo la eligió. Tiempo de caso: solo la clasificación. Tiempo general: carga más casos.</p>
  <div class="cards" id="cards"></div>
  <section class="panel"><h2>Tiempo por caso</h2><div id="tiempo"></div></section>
  <section class="panel"><h2>Precisión por caso</h2><div id="precision"></div></section>
  <section class="panel"><h2>Precisión y tiempo por caso</h2><div id="ambos-caso"></div></section>
  <section class="panel"><h2>Precisión y tiempo general</h2><div id="ambos"></div></section>
  <section class="panel"><h2>Precisión por área</h2><div id="areas"></div></section>
  <section class="panel"><h2>Detalle</h2><div id="tabla"></div></section>
</main>
<script>
const report = /*__DATA__*/;
const models = report.modelos;
const names = models.map((m) => m.nombre);
const cases = models[0].casos.map((row) => row.caso);
const colors = ["#5B8DEF", "#3DDC97"];
const base = {
  chart: { background: "transparent", foreColor: "#e8eef6", toolbar: { show: true }, fontFamily: "Segoe UI, sans-serif" },
  theme: { mode: "dark" },
  colors,
  grid: { borderColor: "#2c3848" },
  legend: { position: "top" },
  dataLabels: { enabled: true },
};

function chart(el, options) {
  new ApexCharts(document.querySelector(el), options).render();
}

document.getElementById("cards").innerHTML = models.map((model) => `
  <article class="card">
    <h2>${model.nombre}</h2>
    <p class="num">${model.precision}% · ${model.general_s}s</p>
    <p class="sub">${model.aciertos}/${model.total} casos · carga ${model.carga_s}s · inferencia ${model.inferencia_s}s</p>
  </article>
`).join("");

chart("#tiempo", {
  ...base,
  series: models.map((model) => ({ name: model.nombre, data: model.casos.map((row) => row.segundos) })),
  chart: { ...base.chart, type: "bar", height: 360 },
  plotOptions: { bar: { borderRadius: 4, columnWidth: "55%" } },
  xaxis: { categories: cases },
  yaxis: { title: { text: "Segundos" }, decimalsInFloat: 1 },
  tooltip: { y: { formatter: (value) => value.toFixed(2) + " s" } },
});

chart("#precision", {
  ...base,
  series: models.map((model) => ({ name: model.nombre, data: model.casos.map((row) => row.precision) })),
  chart: { ...base.chart, type: "bar", height: 360 },
  plotOptions: { bar: { borderRadius: 4, columnWidth: "55%" } },
  xaxis: { categories: cases },
  yaxis: { min: 0, max: 100, title: { text: "Precisión %" } },
  tooltip: { y: { formatter: (value) => value + "%" } },
});

chart("#ambos-caso", {
  ...base,
  series: [
    ...models.map((model) => ({ name: model.nombre + " tiempo (s)", type: "column", data: model.casos.map((row) => row.segundos) })),
    ...models.map((model) => ({ name: model.nombre + " precisión (%)", type: "line", data: model.casos.map((row) => row.precision) })),
  ],
  chart: { ...base.chart, type: "line", height: 400 },
  stroke: { width: [0, 0, 3, 3], curve: "smooth" },
  markers: { size: [0, 0, 5, 5] },
  plotOptions: { bar: { borderRadius: 4, columnWidth: "55%" } },
  colors: ["#5B8DEF", "#3DDC97", "#8FB4F5", "#F0C14D"],
  xaxis: { categories: cases },
  yaxis: [
    { seriesName: models[0].nombre + " tiempo (s)", title: { text: "Segundos" }, decimalsInFloat: 1 },
    { seriesName: models[0].nombre + " tiempo (s)", show: false, decimalsInFloat: 1 },
    { seriesName: models[0].nombre + " precisión (%)", opposite: true, min: 0, max: 100, title: { text: "Precisión %" } },
    { seriesName: models[0].nombre + " precisión (%)", opposite: true, show: false, min: 0, max: 100 },
  ],
  tooltip: { shared: true, intersect: false },
});

chart("#ambos", {
  ...base,
  series: [
    { name: "Tiempo general (s)", type: "column", data: models.map((model) => model.general_s) },
    { name: "Precisión (%)", type: "line", data: models.map((model) => model.precision) },
  ],
  chart: { ...base.chart, type: "line", height: 380 },
  stroke: { width: [0, 3], curve: "smooth" },
  markers: { size: [0, 6] },
  plotOptions: { bar: { borderRadius: 6, columnWidth: "40%" } },
  colors: ["#5B8DEF", "#F0C14D"],
  xaxis: { categories: names },
  yaxis: [
    { title: { text: "Segundos" }, decimalsInFloat: 1 },
    { opposite: true, min: 0, max: 100, title: { text: "Precisión %" } },
  ],
  dataLabels: {
    enabled: true,
    enabledOnSeries: [0, 1],
    formatter: (value, opts) => opts.seriesIndex === 1 ? value + "%" : value + "s",
  },
});

const areaNames = report.areas;
chart("#areas", {
  ...base,
  series: models.map((model) => ({
    name: model.nombre,
    data: areaNames.map((area) => {
      const found = model.por_area.find((item) => item.area === area);
      return found && found.precision !== null ? found.precision : null;
    }),
  })),
  chart: { ...base.chart, type: "bar", height: 380 },
  plotOptions: { bar: { borderRadius: 4, columnWidth: "55%" } },
  xaxis: { categories: areaNames, labels: { rotate: -25, hideOverlappingLabels: false } },
  yaxis: { min: 0, max: 100, title: { text: "Precisión %" } },
  tooltip: { y: { formatter: (value) => value === null || value === undefined ? "sin predicciones" : value + "%" } },
});

const header = `<tr><th>Caso</th><th>Modelo</th><th>Esperado</th><th>Área</th><th>Precisión</th><th>Tiempo</th></tr>`;
const body = models.flatMap((model) => model.casos.map((row) => {
  const mark = row.ok ? "ok" : "bad";
  const label = row.error ? "error" : (row.ok ? "100%" : "0%");
  return `<tr><td>${row.caso}</td><td>${model.nombre}</td><td>${row.esperado || ""}</td><td>${row.area || ""}</td><td class="${mark}">${label}</td><td>${row.segundos.toFixed(2)} s</td></tr>`;
})).join("");
document.getElementById("tabla").innerHTML = `<table><thead>${header}</thead><tbody>${body}</tbody></table>`;
</script>
</body>
</html>
"""


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
