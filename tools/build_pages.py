#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build GitHub Pages directly from the README and current catalog.

No separately maintained copy of the catalog or guide. Only used images are
packaged; models/source/docs link to this repository. Original images are kept
unchanged; WebP derivatives preserve the canvas color in the site's surrounds.
"""
from pathlib import Path
from urllib.parse import quote, urlsplit
from html import escape
from html.parser import HTMLParser
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


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    images = {}

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
            if tag == 'img':
                attrs = re.sub(r'\swidth="[^"]*"', '', attrs)
                attrs += f' width="{info["width"]}" height="{info["height"]}" loading="lazy" decoding="async" style="--canvas:{info["canvas"]}"'
                if path.endswith('project-icon.png'):
                    attrs = attrs.replace('loading="lazy"', 'fetchpriority="high"')
        elif path.endswith('.3mf'):
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
    video = f'''<video id="insertion-demo" class="insertion-video" width="720" height="720" muted playsinline preload="metadata" poster="{poster['url']}" aria-label="A whole Instax Mini photo loads from below at a rear angle, then the frame turns to a close front view">
      <source src="{videos['photo-insertion.webm']}" type="video/webm">
      <source src="{videos['photo-insertion.mp4']}" type="video/mp4">
      <a href="{videos['photo-insertion.mp4']}">Watch the photo insertion animation</a>
    </video>'''
    hero = re.sub(r'<img[^>]*>', lambda _: video, hero, count=1)
    hero = hero.replace('Segmental Arch · actual frame mesh, simulated photo', 'Actual 3D model · rear loading view to front display')
    intro_html = render(intro)
    # The README supplies section headings, text, tables, illustrations, licenses
    # and download/view links. Site-specific content is presentation/navigation.
    start = source.index('![All eight current frames')
    body = source[start:]
    sections = re.split(r'<a name="([^"]+)"></a>', body)
    content = '<section class="overview" aria-label="All eight frames">' + render(sections[0]) + '</section>'
    for anchor, text in zip(sections[1::2], sections[2::2]):
        html = render(text)
        if anchor == 'choose-a-frame':
            html = html.replace('<table>', '<table class="frame-catalog">', 1)
        content += f'<section id="{escape(anchor)}" class="readme-section">{html}</section>'
    count = len(json.loads((ROOT / 'catalog/current.json').read_text())['frames'])
    resources = {}
    for name in ['style.css', 'catalog.js']:
        original = ROOT / 'website' / name
        digest = hashlib.sha256(original.read_bytes()).hexdigest()[:12]
        filename = Path(name).stem + '-' + digest + Path(name).suffix
        shutil.copy2(original, OUT / filename)
        resources[name] = filename
    template = (ROOT / 'website/index.template.html').read_text()
    for key, value in {'TITLE': escape(title), 'HEADING': escape(title).replace('Instax Frames', '<br><em>Instax Frames.</em>'), 'HERO': hero, 'INTRO': intro_html, 'CONTENT': content,
                       'REPO': REPO, 'URL': URL, 'COUNT': str(count), 'STYLE': resources['style.css'], 'SCRIPT': resources['catalog.js']}.items():
        template = template.replace('{{' + key + '}}', value)
    (OUT / 'index.html').write_text(template)
    icon = asset('assets/brand/project-icon.png')
    with Image.open(OUT / icon['url']) as im:
        im.resize((96, 96), Image.Resampling.LANCZOS).save(OUT / 'favicon.png')
    shutil.copy2(OUT / icon['url'], OUT / 'social-preview.webp')
    (OUT / '.nojekyll').touch()
    (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {URL}sitemap.xml\n')
    (OUT / 'sitemap.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{URL}</loc></url></urlset>\n')
    (OUT / 'build-info.json').write_text(json.dumps({'readme_sha256': hashlib.sha256(source.encode()).hexdigest(),
                                                   'catalog_sha256': hashlib.sha256((ROOT/'catalog/current.json').read_bytes()).hexdigest(),
                                                   'frames': count, 'image_count': len(images)}, indent=2) + '\n')
    verify()
    print(f'Built {count} frames from README; {len(images)} optimized images → {OUT}')


def verify():
    class Links(HTMLParser):
        def __init__(self):
            super().__init__(); self.targets=[]; self.ids=set(); self.downloads=[]
        def handle_starttag(self, tag, pairs):
            attrs=dict(pairs)
            assert '/' not in attrs, 'Malformed self-closing image'
            if 'id' in attrs: self.ids.add(attrs['id'])
            for key in ('src', 'href', 'poster'):
                if key in attrs: self.targets.append(attrs[key])
            if attrs.get('href','').endswith('.3mf'): self.downloads.append(attrs['href'])
    doc=Links(); doc.feed((OUT/'index.html').read_text())
    for target in doc.targets:
        if target.startswith('#'):
            assert target[1:] in doc.ids, 'Missing anchor: '+target
        elif not urlsplit(target).scheme:
            assert (OUT/target).is_file(), 'Missing site asset: '+target
    assert len(doc.downloads)==8, 'Expected eight model downloads'
    assert all('/main/models/current/' in p for p in doc.downloads), 'Stale model download'
    assert '{{' not in (OUT/'index.html').read_text(), 'Unresolved template'
    print('PASS site assets, internal anchors and all eight current model links')


if __name__=='__main__':
    build()
