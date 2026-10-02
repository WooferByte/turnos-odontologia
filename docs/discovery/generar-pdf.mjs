// Genera informe-discovery.pdf a partir de informe-discovery.md.
// Uso: node docs/discovery/generar-pdf.mjs
// Requiere Node y Microsoft Edge o Google Chrome instalados. No usa dependencias.
import { readFileSync, writeFileSync, existsSync, mkdtempSync, copyFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { tmpdir } from 'node:os';

const dir = dirname(fileURLToPath(import.meta.url));
const origen = join(dir, 'informe-discovery.md');
const destino = join(dir, 'informe-discovery.pdf');

const escapar = (t) => t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

function enLinea(texto) {
  // Los asteriscos escapados (\*) se protegen para que no se lean como cursiva.
  let t = escapar(texto).replace(/\\\*/g, '\u0001');
  t = t.replace(/`([^`]+)`/g, '<code>$1</code>');
  t = t.replace(/\[([^\]]+)\]\((https?:[^)\s]+)\)/g, '<a href="$2">$1</a>');
  t = t.replace(/(^|[\s(])(https?:\/\/[^\s<)]+[^\s<).,;:])/g, '$1<a href="$2">$2</a>');
  t = t.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  t = t.replace(/(^|[^*])\*([^*\s][^*]*)\*/g, '$1<em>$2</em>');
  return t.replace(/\u0001/g, '*');
}

const celdas = (linea) => linea.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((c) => c.trim());

function convertir(md) {
  const lineas = md.replace(/\r\n/g, '\n').split('\n');
  const html = [];
  let i = 0;
  let portadaCerrada = false;
  while (i < lineas.length) {
    const l = lineas[i];
    if (!l.trim()) { i++; continue; }
    const titulo = l.match(/^(#{1,6})\s+(.*)$/);
    if (titulo) {
      const n = titulo[1].length;
      html.push(`<h${n}>${enLinea(titulo[2])}</h${n}>`);
      i++; continue;
    }
    if (/^---+\s*$/.test(l)) {
      // La primera línea horizontal cierra la portada.
      html.push(portadaCerrada ? '<hr>' : '<div class="salto"></div>');
      portadaCerrada = true;
      i++; continue;
    }
    if (l.startsWith('|') && /^\|?[\s:|-]+$/.test(lineas[i + 1] || '')) {
      const cabecera = celdas(l);
      i += 2;
      const filas = [];
      while (i < lineas.length && lineas[i].startsWith('|')) { filas.push(celdas(lineas[i])); i++; }
      const ancha = cabecera.length > 6 ? ' class="ancha"' : '';
      let t = `<table${ancha}>`;
      if (cabecera.some((c) => c)) t += '<thead><tr>' + cabecera.map((c) => `<th>${enLinea(c)}</th>`).join('') + '</tr></thead>';
      t += '<tbody>' + filas.map((f) => '<tr>' + [...f, ...Array(Math.max(0, cabecera.length - f.length)).fill('')].slice(0, cabecera.length).map((c) => `<td>${enLinea(c)}</td>`).join('') + '</tr>').join('') + '</tbody></table>';
      html.push(t);
      continue;
    }
    if (l.startsWith('>')) {
      const cita = [];
      while (i < lineas.length && lineas[i].startsWith('>')) { cita.push(lineas[i].replace(/^>\s?/, '')); i++; }
      html.push(`<blockquote>${enLinea(cita.join(' '))}</blockquote>`);
      continue;
    }
    const esVineta = (x) => /^\s*[-*]\s+/.test(x);
    const esNumero = (x) => /^\s*\d+\.\s+/.test(x);
    if (esVineta(l) || esNumero(l)) {
      const ordenada = esNumero(l);
      const es = ordenada ? esNumero : esVineta;
      const items = [];
      while (i < lineas.length && es(lineas[i])) {
        items.push(lineas[i].replace(/^\s*(?:[-*]|\d+\.)\s+/, ''));
        i++;
      }
      const etiqueta = ordenada ? 'ol' : 'ul';
      html.push(`<${etiqueta}>` + items.map((x) => `<li>${enLinea(x)}</li>`).join('') + `</${etiqueta}>`);
      continue;
    }
    const parrafo = [];
    while (i < lineas.length && lineas[i].trim() && !/^(#{1,6}\s|\||>|---+\s*$|\s*[-*]\s+|\s*\d+\.\s+)/.test(lineas[i])) {
      parrafo.push(lineas[i]); i++;
    }
    html.push(`<p>${enLinea(parrafo.join(' '))}</p>`);
  }
  return html.join('\n');
}

const estilos = `
@page { size: A4 landscape; margin: 14mm 12mm; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10pt; line-height: 1.4; color: #1a1a1a; }
h1 { font-size: 24pt; margin: 40mm 0 4mm; }
h1 + h2 { font-size: 14pt; font-weight: normal; border: 0; margin: 0 0 12mm; }
h2 { font-size: 15pt; margin: 8mm 0 3mm; padding-bottom: 1mm; border-bottom: 1px solid #999; break-after: avoid; }
h3 { font-size: 12pt; margin: 6mm 0 2mm; break-after: avoid; }
p, li { orphans: 3; widows: 3; }
table { border-collapse: collapse; width: 100%; margin: 3mm 0 5mm; font-size: 8pt; }
table.ancha { font-size: 6.5pt; }
th, td { border: 1px solid #b5b5b5; padding: 1.2mm 1.5mm; vertical-align: top; text-align: left; overflow-wrap: break-word; }
th { background: #e9eef5; }
thead { display: table-header-group; }
tr { break-inside: avoid; }
code { font-family: Consolas, monospace; font-size: 0.92em; background: #f1f1f1; padding: 0 2px; }
blockquote { margin: 3mm 0; padding: 2mm 4mm; border-left: 3px solid #7a8fb0; background: #f5f7fa; }
a { color: #1a4f8b; text-decoration: none; overflow-wrap: anywhere; }
hr { border: 0; border-top: 1px solid #ccc; margin: 6mm 0; }
.salto { break-after: page; }
`;

const cuerpo = convertir(readFileSync(origen, 'utf8'));
const pagina = `<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Informe de Discovery</title><style>${estilos}</style></head><body>${cuerpo}</body></html>`;

const navegador = [
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
].find(existsSync);
if (!navegador) throw new Error('No se encontró Edge ni Chrome para imprimir el PDF.');

// Se trabaja en una carpeta temporal para evitar problemas con rutas con acentos o espacios.
const tmp = mkdtempSync(join(tmpdir(), 'informe-'));
const htmlTmp = join(tmp, 'informe.html');
const pdfTmp = join(tmp, 'informe.pdf');
writeFileSync(htmlTmp, pagina, 'utf8');
execFileSync(navegador, [
  '--headless', '--disable-gpu', '--no-pdf-header-footer',
  `--user-data-dir=${join(tmp, 'perfil')}`,
  `--print-to-pdf=${pdfTmp}`, pathToFileURL(htmlTmp).href,
], { stdio: 'ignore' });
copyFileSync(pdfTmp, destino);
console.log('PDF generado en', destino);
