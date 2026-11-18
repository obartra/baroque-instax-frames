# Discovery and launch notes

Updated 2026-11-18.

## Current improvements

- Exact Instax Mini wording in the collection's search title and description.
- Eight linked design pages, each with its own canonical URL, useful shape/fit notes, current downloads, dimensions and views. Shared facts come from the catalog.
- A nine-URL sitemap; collection and design structured data describe the actual free files without invented prices or ratings.
- A photo-led shape guide in the README/site, with rounded visible-image area from the catalog: about 93% for rectangles, 91% for the other shaped corners and 73% for ovals. Design pages show their own crop and three relevant, illustrated alternatives with orientation/crop context.
- Image sitemap entries for 34 current views, checked against the built assets, plus explicit representative-image and social preview metadata on the design pages. This follows Google's image discovery guidance; it does not guarantee indexing or ranking.
- A 1200 × 630 sharing card rendered from the current Segmental Arch CAD. It is labeled as a render with a simulated photo.
- The same card is saved as GitHub's custom repository social preview, replacing the default avatar/text card. Verified through the repository settings and GitHub's `usesCustomOpenGraphImage` field on 2026-11-18.
- A current eight-design release with separate 3MF, STL and complete downloads, checksums, instructions and license details.
- Responsive lossless WebP previews at 480/640/960 pixels, with full-size enlargement links retained. The eight default angled previews total 407 KB at 480 px or 644 KB at 640 px, compared with 823 KB previously (51% / 22% less image data). Browser checks cover all four shared views and individual design pages. These are file-transfer measurements, not a measured ranking or page-speed gain.
- Google Search Console URL-prefix ownership verified with the personal Google account. The work account and its verification token were removed. The personal verification tag remains in the home template. The nine-page sitemap was submitted; the initial Google fetch reported “couldn’t fetch” although live HTTP/XML checks passed. The homepage indexing request was accepted into the priority crawl queue. Check Search Console for the next processing result; neither submission establishes indexing.

## Mobile audit and print feedback

A PageSpeed Insights mobile lab audit on 2026-11-18 scored performance 97,
accessibility 100, best practices 100 and basic SEO 100. It reported no real-user
field data. See [the recorded conditions and report](performance/mobile-2026-11-18.json).
These scores are not search rankings or a complete accessibility assessment.

The follow-up adds 320 px lossless previews, corrects mobile image sizing for the
actual content width and card gaps, preloads the hero still, and defers video
sources until visible with motion allowed. The eight 320 px default previews
total 211,664 bytes versus 406,730 bytes at 480 px (48% less); the browser still
chooses larger variants when its display needs them. Full-size links stay intact.
GitHub Pages controls the host cache headers; the hosting remains unchanged.

The README/site and all design pages also link to print sharing on the model
platforms and the GitHub print/fit report. Design pages prefill the design name.
GitHub issues were disabled; the tracker was enabled and a prefilled Segmental
Arch report form was verified before publishing the links. No makes, reviews
or issue submissions are posted automatically.

## Next, when more prints and photos are available

The user is still printing examples and making assembly videos; these assets
are intentionally pending, with no immediate delivery date required. The CAD
intro remains explicitly labeled as a simulated-photo render in the meantime.

1. Photograph two or three complete frames containing real photos, on a plain magnetic surface in indirect daylight. Include a close relief view and a rear loading view. Use the strongest assembled photograph for the collection's web and app covers; keep the renders as the comparison gallery.
2. Add a matching photographed MakerWorld profile for Portrait Oval, then the other designs as they are physically printed. Keep each profile's scope and photos aligned with the design it contains.
3. Film a short loading-and-display demonstration: intact film, slide, turn, magnet attachment. Reuse it in the listings and a small number of relevant community posts, following each community's rules. Publish only with the user's authorization.
4. Add the user-approved real photographs to the website with captions identifying the printed design and revision. Photographing people inside an Instax image is optional; landscapes work too.

## Measure before changing presentation again

After enough visits accumulate, compare website search impressions, queries and clicks in Search Console with model-page views, downloads and actual prints in the publishing platforms. Do not treat a single day's counts as a reliable result.

- Few impressions: review indexing, descriptive titles, useful content and relevant links from other sites.
- Views but few downloads: improve the cover's clarity and make fit, required magnets and file choice easier to understand.
- Downloads but few prints: prioritize the missing photographed print profiles and investigate any assembly feedback.

Keep a record of cover/title changes and their dates. These are practical experiments, not guarantees about a platform's private ranking algorithm.

## References

- [Google title-link guidance](https://developers.google.com/search/docs/appearance/title-link)
- [Google Search Console](https://developers.google.com/search/docs/monitor-debug/search-console-start)
- [Google sitemap submission](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)
- [Video loading and poster-priority guidance](https://web.dev/articles/lazy-loading-video)
- [Google image discovery and landing-page guidance](https://developers.google.com/search/docs/appearance/google-images)
- [Google contextual internal-link guidance](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)
- [MakerWorld's published real-photo recommendation update](https://forum.bambulab.com/t/makerworld-release-note-08-29/95806)

Google’s live URL inspection of the sitemap on 2026-11-18 confirmed crawl allowed, page fetch successful and indexing allowed. The earlier sitemap-report fetch error is not reproduced by this live Google test; the submitted sitemap still needs processing.

A later check on 2026-11-18 still showed “couldn't fetch” in the sitemap report,
with no last-read date. No repeat submission was made. Both public model listings
were audited again: current descriptions, film compatibility, magnet size,
license, source links and the Botanical Garland photographs are present. The
photo/video additions above remain waiting on the user's physical examples.
