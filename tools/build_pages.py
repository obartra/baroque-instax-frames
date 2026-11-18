#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build GitHub Pages directly from the README and current catalog.

No separately maintained copy of the catalog or guide. Only used images are
packaged; models/source/docs link to this repository. Original images are kept
unchanged; WebP derivatives preserve the canvas color in the site's surrounds.
"""
from pathlib import Path
from urllib.parse import quote, urlencode, urlsplit
from html import escape
from html.parser import HTMLParser
from xml.etree import ElementTree as ET
import hashlib
import json
import re
import shutil
import markdown
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dist'
REPO = 'https://github.com/obartra/baroque-instax-frames'
URL = 'https://obartra.github.io/baroque-instax-frames/'
SEO_TITLE = 'Free Instax Mini Magnetic Photo Frames — STL & 3MF'
DESCRIPTION = 'Eight free floral Instax Mini magnetic photo frames. Download STL or Bambu Studio 3MF files, keep the film uncut, and assemble with three hidden magnets.'


def json_script(value):
    return json.dumps(value, ensure_ascii=False).replace('<', '\\u003c')


def frame_url(frame):
    return URL + 'frames/' + frame['slug'] + '/'


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    images = {}
    frames = json.loads((ROOT / 'catalog/current.json').read_text())['frames']
    frame_images = {path for frame in frames for path in frame['views'].values()}
    notes = json.loads((ROOT / 'website/frame-notes.json').read_text())
    assert set(notes) == {f['slug'] for f in frames}, 'Missing design-page copy'
    for slug, note in notes.items():
        choices=note['related']
        slugs={choice['slug'] for choice in choices}
        assert len(choices)==len(slugs)==3 and slug not in slugs and slugs<=set(notes), 'Invalid related frame choices'
        assert all(choice['reason'].strip() for choice in choices), 'Missing comparison context'

    def asset(path):
        if path in images:
            return images[path]
        original = (ROOT / path).resolve()
        if not original.is_relative_to(ROOT) or not original.is_file():
            raise ValueError('Missing or unsafe image: ' + path)
        digest = hashlib.sha256(original.read_bytes()).hexdigest()[:12]
        target = Path('media') / Path(path).with_name(Path(path).stem + '-' + digest + '.webp')
        (OUT / target).parent.mkdir(parents=True, exist_ok=True)
        with Image.open(original) as im:
            im = im.convert('RGB')
            canvas = '#%02x%02x%02x' % im.getpixel((0, 0))
            im.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
            # Lossless export keeps the exact flat background color.
            im.save(OUT / target, 'WEBP', lossless=True, method=4)
            info = dict(url=target.as_posix(), width=im.width, height=im.height, canvas=canvas)
            variants = []
            for width in (320, 480, 640, 960):
                if width >= im.width:
                    continue
                small = im.resize((width, round(im.height * width / im.width)), Image.Resampling.LANCZOS)
                variant = target.with_stem(target.stem + f'-{width}w')
                small.save(OUT / variant, 'WEBP', lossless=True, method=4)
                variants.append((variant.as_posix(), width))
            variants.append((info['url'], info['width']))
            info['variants'] = variants
        images[path] = info
        return info

    def rewrite_link(match):
        tag, attrs = match.group(1), match.group(2).rstrip().removesuffix('/').rstrip()
        key = 'src' if tag == 'img' else 'href'
        found = re.search(rf'\b{key}="([^"]+)"', attrs)
        if not found:
            return match.group(0)
        path = found.group(1)
        if urlsplit(path).scheme or path.startswith('#'):
            return match.group(0)
        if path.lower().endswith(('.png', '.jpg', '.jpeg')):
            info = asset(path)
            target = info['url']
            attrs += f' data-canvas="{info["canvas"]}"'
            srcset = ', '.join(f'{url} {width}w' for url, width in info['variants'])
            if tag == 'a':
                attrs += f' data-srcset="{srcset}"'
            if tag == 'img':
                attrs = re.sub(r'\swidth="[^"]*"', '', attrs)
                attrs += f' width="{info["width"]}" height="{info["height"]}" loading="lazy" decoding="async" style="--canvas:{info["canvas"]}"'
                sizes = ('(max-width: 700px) calc(44vw - 9px), (max-width: 1000px) calc(30.667vw - 18.667px), (max-width: 1320px) calc(23vw - 21px), 283px'
                         if path in frame_images else '(max-width: 700px) 88vw, (max-width: 1320px) 92vw, 1215px')
                attrs += f' srcset="{srcset}" sizes="{sizes}"'
                if path.endswith('project-icon.png'):
                    attrs = attrs.replace('loading="lazy"', 'fetchpriority="high"')
        elif path.endswith(('.3mf', '-stl.zip')):
            target = REPO.replace('github.com', 'raw.githubusercontent.com') + '/main/' + quote(path)
            attrs += ' class="download-link"'
        else:
            kind = 'tree' if (ROOT / path.split('#', 1)[0]).is_dir() else 'blob'
            target = REPO + '/' + kind + '/main/' + quote(path, safe='/#')
        attrs = attrs[:found.start(1)] + escape(target, quote=True) + attrs[found.end(1):]
        return f'<{tag}{attrs}>'

    def render(text):
        text = text.replace('<details>', '<details markdown="1">')
        html = markdown.markdown(text, extensions=['extra'])
        return re.sub(r'<(a|img)(\s[^>]*?)>', rewrite_link, html)

    source = (ROOT / 'README.md').read_text()
    title = source.splitlines()[0].removeprefix('# ')
    intro = re.search(r'(Eight floral frames.*?)(?:\n\n)', source, re.S).group(1)
    hero = re.search(r'<p align="center">.*?</p>', source, re.S).group(0)
    hero = hero.replace('align="center"', 'class="hero-image"')
    hero = render(hero)
    poster = asset('assets/demo/photo-insertion-poster.png')
    videos = {}
    for name in ['photo-insertion.mp4', 'photo-insertion.webm']:
        original = ROOT / 'assets/demo' / name
        digest = hashlib.sha256(original.read_bytes()).hexdigest()[:12]
        filename = Path(name).stem + '-' + digest + Path(name).suffix
        target = OUT / 'media/assets/demo' / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, target)
        videos[name] = target.relative_to(OUT).as_posix()
    video = f'''<span class="insertion-scene" role="img" aria-label="Segmental Arch frame holding an uncut Instax Mini photo; the rear channel lets the whole photo slide out and back in."><video id="insertion-demo" class="insertion-video" width="720" height="720" muted playsinline preload="none" poster="{poster['url']}" aria-hidden="true">
      <source data-src="{videos['photo-insertion.webm']}" type="video/webm">
      <source data-src="{videos['photo-insertion.mp4']}" type="video/mp4">
    </video><img class="insertion-poster" src="{poster['url']}" srcset="{poster['url']} 720w" sizes="(max-width: 700px) 88vw, 540px" width="720" height="720" alt="" aria-hidden="true" fetchpriority="high"></span>'''
    hero = re.sub(r'<img[^>]*>', lambda _: video, hero, count=1)
    hero = hero.replace('Segmental Arch · actual frame mesh, simulated photo', 'Actual 3D model · simulated photo')
    intro_html = render(intro)
    # The README supplies section headings, text, tables, illustrations, licenses
    # and download/view links. Site-specific content is presentation/navigation.
    start = source.index('![All eight current frames')
    body = source[start:]
    sections = re.split(r'<a name="([^"]+)"></a>', body)
    content = '<section class="overview" aria-label="All eight frames">' + render(sections[0]) + '</section>'
    for anchor, text in zip(sections[1::2], sections[2::2]):
        html = render(text)
        if anchor == 'print-and-assemble':
            html = html.replace('<p><strong>Printed one?</strong>', '<p class="print-feedback"><strong>Printed one?</strong>')
        if anchor == 'choose-a-frame':
            html = html.replace('<table>', '<table class="frame-catalog">', 1)
            html = html.replace('Click a preview to enlarge; use the view links for other angles.',
                                'Choose a view to compare all eight frames from the same angle. Click any preview to enlarge.')
            for frame in frames:
                name = escape(frame['name'])
                html = html.replace(f'<strong>{name}</strong>',
                                    f'<a class="frame-title" href="frames/{frame["slug"]}/"><strong>{name}</strong></a>', 1)
        content += f'<section id="{escape(anchor)}" class="readme-section">{html}</section>'
    count = len(frames)
    resources = {}
    for name in ['style.css', 'catalog.js']:
        original = ROOT / 'website' / name
        digest = hashlib.sha256(original.read_bytes()).hexdigest()[:12]
        filename = Path(name).stem + '-' + digest + Path(name).suffix
        shutil.copy2(original, OUT / filename)
        resources[name] = filename
    template = (ROOT / 'website/index.template.html').read_text()
    structured = {'@context': 'https://schema.org', '@type': 'CollectionPage',
                  '@id': URL, 'url': URL, 'name': SEO_TITLE, 'description': DESCRIPTION,
                  'image': URL + 'social-preview.png',
                  'primaryImageOfPage': URL + 'social-preview.png',
                  'mainEntity': {'@type': 'ItemList', 'numberOfItems': count,
                                 'itemListElement': [{'@type': 'ListItem', 'position': i,
                                                      'name': frame['name'], 'url': frame_url(frame)}
                                                     for i, frame in enumerate(frames, 1)]}}
    for key, value in {'TITLE': escape(title), 'HEADING': escape(title).replace('Instax Frames', '<br><em>Instax Frames.</em>'), 'HERO': hero, 'INTRO': intro_html, 'CONTENT': content, 'HERO_POSTER': poster['url'],
                       'REPO': REPO, 'URL': URL, 'COUNT': str(count), 'STYLE': resources['style.css'], 'SCRIPT': resources['catalog.js'],
                       'SEO_TITLE': escape(SEO_TITLE), 'DESCRIPTION': escape(DESCRIPTION),
                       'STRUCTURED_DATA': json_script(structured)}.items():
        template = template.replace('{{' + key + '}}', value)
    (OUT / 'index.html').write_text(template)
    icon = asset('assets/brand/project-icon.png')
    with Image.open(OUT / icon['url']) as im:
        im.resize((96, 96), Image.Resampling.LANCZOS).save(OUT / 'favicon.png')
    shutil.copy2(OUT / icon['url'], OUT / 'social-preview.webp')
    shutil.copy2(ROOT / 'assets/brand/social-preview.png', OUT / 'social-preview.png')
    with Image.open(OUT / 'social-preview.png') as im:
        assert im.size == (1200, 630), 'Sharing preview dimensions'
    for frame in frames:
        write_frame_page(frame, notes[frame['slug']], asset, resources)
    (OUT / '.nojekyll').touch()
    (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {URL}sitemap.xml\n')
    urls = [URL] + [frame_url(frame) for frame in frames]
    page_images = {URL: [URL + asset('renders/Eight-frames-current.png')['url'], URL + poster['url']]}
    page_images.update({frame_url(frame): [URL + asset(path)['url'] for path in frame['views'].values()] for frame in frames})
    (OUT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">'
                                   + ''.join(f'<url><loc>{escape(url)}</loc>' + ''.join(f'<image:image><image:loc>{escape(src)}</image:loc></image:image>' for src in page_images[url]) + '</url>' for url in urls) + '</urlset>\n')
    (OUT / 'build-info.json').write_text(json.dumps({'readme_sha256': hashlib.sha256(source.encode()).hexdigest(),
                                                   'catalog_sha256': hashlib.sha256((ROOT/'catalog/current.json').read_bytes()).hexdigest(),
                                                   'frames': count, 'image_count': len(images)}, indent=2) + '\n')
    verify()
    print(f'Built {count} frames from README; {len(images)} optimized images → {OUT}')


def write_frame_page(frame, notes, asset, resources):
    name = frame['name']
    url = frame_url(frame)
    page_title = f'{name} Instax Mini Frame — Free STL & 3MF'
    description = f"Free {frame['orientation']} {name.lower()} magnetic frame for uncut Instax Mini photos. Download STL and 3MF files, with matching back and three magnet pockets."
    view_info = {key: asset(path) for key, path in frame['views'].items()}
    image_url = URL + view_info['front']['url']
    raw = REPO.replace('github.com', 'raw.githubusercontent.com') + '/main/'
    model_url = raw + quote(frame['model'])
    stl_url = raw + quote(frame['stl']['archive'])
    report_url = REPO + '/issues/new?' + urlencode({'template':'print-report.md', 'title':f'[Print report] {name}'})
    structured = {'@context': 'https://schema.org', '@type': 'CreativeWork', '@id': url,
                  'url': url, 'name': f'{name} Instax Mini magnetic photo frame',
                  'description': notes['intro'], 'image': image_url,
                  'license': 'https://creativecommons.org/publicdomain/zero/1.0/',
                  'mainEntityOfPage': {'@type': 'WebPage', '@id': url, 'primaryImageOfPage': image_url},
                  'isPartOf': {'@id': URL},
                  'encoding': [{'@type': 'MediaObject', 'encodingFormat': 'model/3mf', 'contentUrl': model_url},
                               {'@type': 'MediaObject', 'encodingFormat': 'application/zip', 'contentUrl': stl_url}]}

    def image(key, alt, eager=False):
        info = view_info[key]
        loading = 'fetchpriority="high"' if eager else 'loading="lazy"'
        srcset = ', '.join(f'../../{url} {width}w' for url, width in info['variants'])
        sizes = ('(max-width: 700px) 88vw, 560px' if eager
                 else '(max-width: 700px) 88vw, 400px')
        return f'<a href="../../{info["url"]}"><img src="../../{info["url"]}" srcset="{srcset}" sizes="{sizes}" alt="{escape(alt)}" width="{info["width"]}" height="{info["height"]}" {loading} decoding="async" style="--canvas:{info["canvas"]}"></a>'

    def duration(minutes):
        minutes = round(minutes)
        return f'{minutes//60} h {minutes%60:02d} min' if minutes >= 60 else f'{minutes} min'

    width, height = frame['dimensions_mm'][:2]
    orientation = frame['orientation'].capitalize()
    catalog = {f['slug']: f for f in json.loads((ROOT/'catalog/current.json').read_text())['frames']}
    related = []
    for choice in notes['related']:
        other = catalog[choice['slug']]
        info = asset(other['views']['front'])
        srcset = ', '.join(f'../../{url} {width}w' for url, width in info['variants'])
        related.append(f'''<li><a href="../{other['slug']}/"><img src="../../{info['url']}" srcset="{srcset}" sizes="(max-width: 700px) 42vw, 360px" width="{info['width']}" height="{info['height']}" alt="{escape(other['name'])} front render" loading="lazy" decoding="async"><strong>{escape(other['name'])}</strong><span>{escape(choice['reason'])}</span></a></li>''')
    related = ''.join(related)
    document = f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#f6f4ee"><title>{escape(page_title)}</title>
<meta name="description" content="{escape(description)}"><link rel="canonical" href="{url}">
<link rel="icon" type="image/png" href="../../favicon.png">
<meta property="og:type" content="website"><meta property="og:title" content="{escape(page_title)}">
<meta property="og:description" content="{escape(description)}"><meta property="og:url" content="{url}">
<meta property="og:image" content="{image_url}"><meta property="og:image:alt" content="{escape(name)} actual CAD front render">
<meta property="og:image:width" content="{view_info['front']['width']}"><meta property="og:image:height" content="{view_info['front']['height']}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{escape(page_title)}"><meta name="twitter:description" content="{escape(description)}"><meta name="twitter:image" content="{image_url}"><meta name="twitter:image:alt" content="{escape(name)} actual CAD front render">
<link rel="stylesheet" href="../../{resources['style.css']}">
<script type="application/ld+json">{json_script(structured)}</script>
</head><body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><a class="wordmark" href="../../"><span class="brand-mark" aria-hidden="true">❦</span> Floral Instax Frames</a>
<nav aria-label="Main navigation"><a href="../../#choose-a-frame">Collection</a><a href="../../#print-and-assemble">Assembly</a><a href="{REPO}">GitHub ↗</a></nav></header>
<main id="main" class="frame-detail">
<p class="breadcrumbs"><a href="../../">All frames</a> / {escape(name)}</p>
<section class="detail-hero"><div><p class="eyebrow">{orientation} · Free STL &amp; 3MF</p>
<h1>{escape(name)}<br><em>Instax Mini frame</em></h1><p>{escape(notes['intro'])}</p>
<div class="hero-actions"><a class="button primary" href="{model_url}">Download 3MF</a><a class="button secondary" href="{stl_url}">Download STL ZIP</a></div>
<p class="detail-download-note">3MF: matching front and back on two plates.<br>STL ZIP: mat, ornament, back and import guide.</p>
<p><a href="{REPO}/releases/download/v0.2.0/Floral-Instax-Frames-v0.2.0-Two-Color-P2S.zip">Two-color P2S pack · all eight designs with plate previews</a></p>
<p><a href="../../#before-you-print">Print settings and filament changes</a> · <a href="{REPO}/releases/latest">Download all eight designs</a></p></div>
<figure>{image('angle', name + ' Instax Mini frame, upright side perspective showing its thickness', True)}<figcaption>Actual CAD render · example materials</figcaption></figure></section>
<section class="detail-section"><h2>Photo fit and dimensions</h2><p>{escape(notes['fit'])}</p>
<p class="detail-crop">About <strong>{frame['image_visible_percent']:.0f}% of the image area</strong> remains visible through this opening. The complete film sheet stays uncut.</p>
<dl class="frame-specs"><div><dt>Film</dt><dd>Instax Mini · 86 × 54 mm, uncut</dd></div><div><dt>Overall size</dt><dd>{width:.1f} × {height:.1f} mm</dd></div>
<div><dt>Assembled depth</dt><dd>{frame['depth_mm']:.1f} mm</dd></div><div><dt>Magnets</dt><dd>Three <a href="https://www.amazon.com/s?k=6x3mm+neodymium+disc+magnets">6 × 3 mm disc magnets</a></dd></div>
<div><dt>Inner mat</dt><dd>{frame['mat_height_mm']:.2f} mm · {frame['mat_layers']} supplied layers</dd></div><div><dt>Estimated print time</dt><dd>Front {duration(frame['front_minutes'])} · back {duration(frame['back_minutes'])}</dd></div></dl>
<p class="detail-small">Times are slicer estimates for the supplied Bambu P2S / 0.4 mm profile. The shaped opening crops the photograph; the instant film stays whole.</p></section>
<section class="detail-section"><h2>Front, back and full-film fit</h2><div class="detail-gallery">
<figure>{image('front', name + ' magnetic Instax Mini frame front view')}<figcaption>Front · actual CAD render</figcaption></figure>
<figure>{image('back', name + ' matching back with three magnet pockets')}<figcaption>Matching back · three magnet pockets</figcaption></figure>
<figure>{image('fit', name + ' rear drawing showing the complete uncut Instax Mini film behind the frame')}<figcaption>Rear photo-fit drawing · full film sheet</figcaption></figure></div></section>
<section class="detail-section"><h2>Make this frame</h2><ol><li>Print the front and its matching back.</li><li>Glue three magnets into the back pockets.</li><li>Snap the front and back together; the clips may also be glued.</li><li>Slide in the whole photo, narrow-border edge first.</li><li>Place it on a magnetic surface.</li></ol><p><a href="../../#print-and-assemble">Follow the illustrated assembly guide →</a></p>
<p>For other slicers, import the mat and ornament together as parts of one object, preserving their coordinates. Print the back separately. <a href="{REPO}/blob/main/docs/PRINTING.md#using-the-stl-downloads">STL alignment and color-change guide</a>.</p></section>
<aside class="print-feedback"><strong>Printed this frame?</strong><a href="https://www.printables.com/model/1920140-rococo-instax-mini-magnetic-frames-8-designs/comments">Share a make on Printables</a><a href="https://makerworld.com/en/models/3636176-rococo-instax-mini-magnetic-frames-8-designs">Share on MakerWorld</a><a href="{escape(report_url,quote=True)}">Report a print or fit issue</a></aside>
<section class="detail-section"><h2>Compare other shapes</h2><ul class="related-frames">{related}</ul><p><a href="../../#choose-a-frame">See all eight designs →</a></p><p>New Rococo-inspired compositions developed with AI-assisted carving studies and custom CAD. Models are free under <a href="{REPO}/blob/main/LICENSING.md">CC0, within the documented license scope</a>.</p></section>
</main><footer><a href="../../">Floral Instax Frames</a><small>Instax is a FUJIFILM trademark; this is an independent project.</small></footer>
</body></html>'''
    target = OUT/'frames'/frame['slug']
    target.mkdir(parents=True)
    (target/'index.html').write_text(document)


def verify():
    class Links(HTMLParser):
        def __init__(self):
            super().__init__(); self.targets=[]; self.ids=set(); self.downloads=[]; self.stls=[]; self.canonicals=[]; self.metas={}; self.title=''; self.schema=''; self.in_title=False; self.in_schema=False
        def handle_starttag(self, tag, pairs):
            attrs=dict(pairs)
            assert '/' not in attrs, 'Malformed self-closing image'
            if 'id' in attrs: self.ids.add(attrs['id'])
            for key in ('src', 'href', 'poster', 'data-src'):
                if key in attrs: self.targets.append(attrs[key])
            for key in ('srcset', 'data-srcset'):
                if key in attrs:
                    for candidate in attrs[key].split(','):
                        target, width = candidate.strip().rsplit(' ', 1)
                        assert re.fullmatch(r'[1-9][0-9]*w', width), 'Invalid responsive image width'
                        self.targets.append(target)
            if attrs.get('href','').endswith('.3mf'): self.downloads.append(attrs['href'])
            if attrs.get('href','').endswith('-stl.zip'): self.stls.append(attrs['href'])
            if tag=='link' and attrs.get('rel')=='canonical': self.canonicals.append(attrs['href'])
            if tag=='meta': self.metas[attrs.get('name',attrs.get('property',''))]=attrs.get('content','')
            if tag=='title': self.in_title=True
            if tag=='script' and attrs.get('type')=='application/ld+json': self.in_schema=True
            if tag=='img':
                assert attrs.get('alt') or (attrs.get('aria-hidden')=='true' and attrs.get('alt')==''), 'Image without alt text'
                assert attrs.get('width') and attrs.get('height'), 'Image without layout dimensions'
                assert attrs.get('srcset') and attrs.get('sizes'), 'Image without responsive sources'
        def handle_endtag(self,tag):
            if tag=='title': self.in_title=False
            if tag=='script': self.in_schema=False
        def handle_data(self,data):
            if self.in_title:self.title+=data
            if self.in_schema:self.schema+=data
    doc=Links(); doc.feed((OUT/'index.html').read_text())
    for target in doc.targets:
        if target.startswith('#'):
            assert target[1:] in doc.ids, 'Missing anchor: '+target
        elif not urlsplit(target).scheme:
            local=OUT/target
            if target.endswith('/'):local=local/'index.html'
            assert local.is_file(), 'Missing site asset: '+target
    assert len(doc.downloads)==8, 'Expected eight model downloads'
    assert all('/main/models/current/' in p for p in doc.downloads), 'Stale model download'
    assert len(doc.stls)==8 and all('/main/models/current/stl/' in p for p in doc.stls), 'Expected eight current STL archives'
    assert '{{' not in (OUT/'index.html').read_text(), 'Unresolved template'
    titles=set(); canonicals=set()
    pages=[OUT/'index.html']+sorted((OUT/'frames').glob('*/index.html'))
    assert len(pages)==9, 'Expected collection and eight design pages'
    for page in pages:
        parsed=Links(); parsed.feed(page.read_text())
        assert parsed.title and parsed.title not in titles, 'Missing/duplicate search title: '+str(page)
        titles.add(parsed.title)
        assert len(parsed.canonicals)==1, 'Canonical URL missing or duplicated'
        canonical=parsed.canonicals[0];canonicals.add(canonical)
        assert parsed.metas.get('description') and parsed.metas.get('og:image') and parsed.metas.get('twitter:card')=='summary_large_image', 'Search/share metadata missing'
        structured=json.loads(parsed.schema)
        assert structured['@id']==canonical, 'Structured data belongs to another page'
        assert 'Instax Mini' in parsed.title, 'Exact film format missing from title'
        if page!=OUT/'index.html':
            assert len(parsed.downloads)==len(parsed.stls)==1, 'Design page download pair missing'
            assert structured['@type']=='CreativeWork' and len(structured['encoding'])==2, 'Design file metadata missing'
        for target in parsed.targets:
            if target.startswith('#'):
                assert target[1:] in parsed.ids, 'Missing design-page anchor: '+target
            elif target.startswith(URL):
                path=target[len(URL):].split('#',1)[0]
                local=OUT/path
                if not path or path.endswith('/'):local=local/'index.html'
                assert local.is_file(), 'Broken internal page/asset: '+target
            elif not urlsplit(target).scheme:
                path=target.split('#',1)[0]
                local=(page.parent/path).resolve()
                if not path or path.endswith('/'):local=local/'index.html'
                assert local.is_relative_to(OUT) and local.is_file(), 'Broken relative page/asset: '+target
    sitemap=ET.fromstring((OUT/'sitemap.xml').read_text())
    urls={node.text for node in sitemap.findall('{*}url/{*}loc')}
    assert urls==canonicals, 'Sitemap differs from canonical page URLs'
    for node in sitemap.findall('{*}url'):
        page_url=node.find('{*}loc').text
        images=node.findall('{http://www.google.com/schemas/sitemap-image/1.1}image/{http://www.google.com/schemas/sitemap-image/1.1}loc')
        assert len(images)==(2 if page_url==URL else 4), 'Missing sitemap views'
        for image in images:
            assert image.text.startswith(URL) and (OUT/image.text[len(URL):]).is_file(), 'Missing sitemap image'
    print('PASS nine unique searchable pages, structured data, sharing metadata, sitemap, internal assets and current downloads')


if __name__=='__main__':
    build()
