"""Behavioral smoke of the delivered file with external network disabled."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json

root = Path(__file__).resolve().parents[1]
artifacts = root / 'artifacts'
artifacts.mkdir(exist_ok=True)
results = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce', accept_downloads=True)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.route('http://**/*', lambda route: route.abort())
    page.route('https://**/*', lambda route: route.abort())
    page.goto((root/'index.html').as_uri())
    page.wait_for_function("document.fonts.status==='loaded' && document.querySelector('.rubbing img').naturalWidth>0")
    assert page.locator('.rubbing img').evaluate('(im)=>im.complete && im.naturalWidth>0')
    for width in (360, 728, 1440):
        page.set_viewport_size({'width': width, 'height': 1000})
        for view in ('landscape','archive','rules'):
            page.locator('#tab-'+view).click()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, view, 'horizontal overflow')
            results.append(f'{width}px {view}: no overflow')
        page.locator('#tab-landscape').click()
        page.screenshot(path=str(artifacts/f'preview-{width}.png'),full_page=True)
    page.locator('#tab-archive').click()
    assert page.locator('.artifact').count() == 9
    page.locator('[data-filter="tour"]').click()
    assert page.locator('.artifact').count() == 2
    page.locator('.artifact button').first.click()
    assert page.locator('#inspector').is_visible()
    page.locator('#inspect-image').evaluate('(im)=>im.decode()')
    page.keyboard.press('Escape')
    assert page.locator('#inspector').is_hidden()
    page.locator('[data-filter="all"]').click()
    assert page.locator('.artifact').count() == 38
    assert page.evaluate("async()=>{const imgs=[...document.querySelectorAll('.artifact img')];imgs.forEach(i=>i.loading='eager');await Promise.all(imgs.map(i=>i.decode()));return imgs.every(i=>i.naturalWidth>0)}")
    page.locator('#tab-landscape').click()
    page.locator('[data-chapter="6"]').click()
    assert page.locator('#chapter-word').inner_text() == '墨中万物'
    page.locator('#theme').click()
    assert page.locator('#study').evaluate("x=>x.classList.contains('paper-mode')")
    page.locator('#theme').click()
    page.locator('#tab-landscape').focus()
    page.keyboard.press('ArrowRight')
    assert page.locator('#tab-archive').get_attribute('aria-selected') == 'true'
    page.locator('#tab-rules').click()
    for key,filename in [('design','DESIGN.md'),('skill','SKILL.md'),('sources','SOURCES.md')]:
        with page.expect_download() as event:
            page.locator(f'[data-download="{key}"]').click()
        download=event.value
        assert download.suggested_filename == filename
        assert Path(download.path()).stat().st_size > 1000
    assert not errors, errors
    results.extend(['38 offline thumbnail images loaded','Offline embedded font loaded','Theme and chapter switching passed','Filter and image inspector passed','Keyboard navigation and Escape passed','All 3 real file downloads passed','No uncaught JavaScript errors'])
    (artifacts/'verification.json').write_text(json.dumps({'passed':True,'results':results,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
    browser.close()
print(json.dumps({'passed':True,'results':results},ensure_ascii=False))
