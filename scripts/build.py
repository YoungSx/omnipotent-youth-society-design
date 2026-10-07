"""Build the offline study and portable skill packages from checked-in inputs."""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
from pathlib import Path
import shutil
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
FONT = ASSETS / "ma-shan-zheng-subset.ttf"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def data_url(path: Path) -> str:
    mime = {".jpg": "image/jpeg", ".png": "image/png", ".ttf": "font/ttf"}[path.suffix]
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def build_gallery(titles: dict[str, str]) -> list[dict[str, str]]:
    manifest = read_json(ROOT / "research/asset-manifest.json")
    rows = [row for row in manifest if row.get("file") and row["category"] != "album-original"]
    gallery = []
    for row in rows:
        original = ROOT / row["file"]
        if not original.is_file():
            raise FileNotFoundError(f"Missing required reference image: {row['file']}")
        thumbnail = ASSETS / f"thumb-{row['id']}.jpg"
        display = ASSETS / f"view-{row['id']}.jpg"
        for destination, size, quality in [(thumbnail, (540, 640), 82), (display, (1200, 1600), 85)]:
            with Image.open(original) as image:
                image = image.convert("RGB")
                image.thumbnail(size)
                image.save(destination, quality=quality, optimize=True)
        category = row["category"]
        note = {"album": "实体资料 / CAA 档案", "tour": "场馆 / 票务视觉", "first-era": "首专时期与设计沿革 / 非二专素材"}[category]
        if row["id"] == "album-scans-08":
            note = "与封面重复 / 非另一套视觉"
        elif row["id"] in ("album-scans-06", "album-scans-07"):
            note = "完整长宽比缩略 / 高清原件来源见档案"
        elif row["id"] == "digital-cover-01":
            note = "数字版本 / 与实体扫描曝光不同"
        gallery.append(dict(id=row["id"], title=titles[row["id"]], note=note, category=category,
                            thumb=relative(thumbnail), full=relative(display), source=row["source"]))
    return gallery


def prepare_skill(documents: dict) -> None:
    refs = ROOT / "skill/references"
    design = documents["design"]["text"].replace("research/SOURCES.md", "SOURCES.md")
    design = design.replace("配套示例：运行 `python build.py` 后打开 `index.html`；源码见 [HTML 模板](page.template.html)。可复用技能：[SKILL.md](skill/SKILL.md)。",
                            "配套的独立 HTML 样本由创建者另行保存；此技能可独立使用。")
    write_text(refs / "DESIGN.md", design)
    write_text(refs / "SOURCES.md", documents["sources"]["text"] +
               "\n注：文中 research/、完整 assets/ 与 HTML 指原研究包；此技能独立携带规范、来源及三张研究参考图。\n")
    destination = ROOT / "skill/assets"
    destination.mkdir(parents=True, exist_ok=True)
    files = [("view-digital-cover-01.jpg", "reference-cover.jpg"),
             ("view-tour-2023-shanghai.jpg", "reference-shanghai.jpg"),
             ("view-tour-2024-taiwan.jpg", "reference-taiwan.jpg"),
             ("FONT-LICENSE.txt", "FONT-LICENSE.txt")]
    for source, name in files:
        shutil.copyfile(ASSETS / source, destination / name)


def render_template(catalog: dict, gallery: list[dict], documents: dict) -> tuple[str, list[str]]:
    template = (ROOT / "page.template.html").read_text(encoding="utf-8")
    chapters = catalog["chapters"]
    tracks = "".join(f'<button data-chapter="{i}" aria-pressed="{str(i == 0).lower()}">'
                     f'<small>{i + 1:02}</small>{html.escape(item["name"])}</button>'
                     for i, item in enumerate(chapters))
    sources = "".join(f'<li><div><a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">'
                      f'{html.escape(title)} ↗</a><p>{html.escape(note)}</p></div></li>'
                      for title, url, note in catalog["source_rows"])
    replacements = {"FONT": data_url(FONT), "TRACKS": tracks, "SOURCES": sources,
                    "CHAPTERS": json.dumps(chapters, ensure_ascii=False),
                    "DOCUMENTS": json.dumps(documents, ensure_ascii=False),
                    "HERO": "assets/digital-cover-01.jpg", "SCROLL": "assets/scroll-web-01.jpg",
                    "GALLERY": json.dumps(gallery, ensure_ascii=False)}
    for key, value in replacements.items():
        template = template.replace(f"%%{key}%%", value)
    paths = {item[key] for item in gallery for key in ("thumb", "full")}
    paths.update([replacements["HERO"], replacements["SCROLL"]])
    return template, sorted(paths, key=lambda path: (-len(path), path))


def embed_assets(template: str, paths: list[str]) -> str:
    embedded = {}
    for index, path in enumerate(paths):
        key = f"img{index}"
        embedded[key] = data_url(ROOT / path)
        template = template.replace(f'src="{path}"', f'data-embedded-src="{key}"')
        template = template.replace(json.dumps(path), f'toBlob({json.dumps(key)})')
    hydration = """
const embedded = __EMBEDDED__;
const blobCache = new Map();
function toBlob(key) {
  if (blobCache.has(key)) return blobCache.get(key);
  const data = embedded[key], comma = data.indexOf(',');
  const mime = data.slice(5, data.indexOf(';'));
  const bytes = Uint8Array.from(atob(data.slice(comma + 1)), c => c.charCodeAt(0));
  const url = URL.createObjectURL(new Blob([bytes], {type: mime}));
  blobCache.set(key, url); return url;
}
document.querySelectorAll('[data-embedded-src]').forEach(img => img.src = toBlob(img.dataset.embeddedSrc));
""".replace("__EMBEDDED__", json.dumps(embedded))
    return template.replace("'use strict';", "'use strict';" + hydration)


def write_archive(path: Path, files: dict[str, Path]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        for name, source in sorted(files.items()):
            entry = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            archive.writestr(entry, source.read_bytes())


def package_outputs() -> None:
    skill = ROOT / "skill"
    files = {f"omnipotent-youth-society-design/{path.relative_to(skill).as_posix()}": path
             for path in skill.rglob("*") if path.is_file()}
    write_archive(ROOT / "dist/omnipotent-youth-society-design.zip", files)
    kit = {f"skill/{path.relative_to(skill).as_posix()}": path
           for path in skill.rglob("*") if path.is_file()}
    for name in ["index.html", "README.md", "DESIGN.md", "research/SOURCES.md",
                 "research/asset-manifest.json", "assets/FONT-LICENSE.txt"]:
        kit[name] = ROOT / name
    write_archive(ROOT / "dist/linlu-design-kit.zip", kit)


def build_site(template: str, paths: list[str]) -> None:
    """Keep web images separately cacheable and URLs relative to the project path."""
    destination = ROOT / "_site"
    write_text(destination / "index.html", template)
    write_text(destination / ".nojekyll", "")
    for path in paths:
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, target)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-skill", action="store_true", help="Explicitly install the built skill into CODEX_HOME/skills.")
    parser.add_argument("--preview", action="store_true", help="Also create an untracked T3 preview with local absolute asset paths.")
    parser.add_argument("--site", action="store_true", help="Build a GitHub Pages site in _site with relative, cacheable image URLs.")
    args = parser.parse_args()
    catalog = read_json(ROOT / "data/catalog.json")
    gallery = build_gallery(catalog["titles"])
    documents = {key: dict(name=name, text=(ROOT / path).read_text(encoding="utf-8")) for key, name, path in [
        ("design", "DESIGN.md", "DESIGN.md"), ("skill", "SKILL.md", "skill/SKILL.md"),
        ("sources", "SOURCES.md", "research/SOURCES.md")]}
    prepare_skill(documents)
    template, paths = render_template(catalog, gallery, documents)
    write_text(ROOT / "index.html", embed_assets(template, paths))
    if args.site:
        build_site(template, paths)
    if args.preview:
        for path in paths:
            template = template.replace(path, (ROOT / path).as_posix())
        write_text(ROOT / "preview.tool.html", template)
    package_outputs()
    result = dict(gallery=len(gallery), html="index.html", archives="dist/", offline_bytes=(ROOT / "index.html").stat().st_size)
    if args.site:
        result["site"] = "_site/"
    if args.install_skill:
        codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
        destination = codex_home / "skills/omnipotent-youth-society-design"
        shutil.copytree(ROOT / "skill", destination, dirs_exist_ok=True)
        result["installed"] = str(destination)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
