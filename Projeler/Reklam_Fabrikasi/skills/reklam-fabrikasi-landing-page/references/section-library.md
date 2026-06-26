# Bölüm Kütüphanesi, HTML + Tailwind Şablonları

Açılış sayfası oluşturmak için gereken her bölüm; marka token kullanımı ve EDIT işaretleriyle birlikte. Bunları başlangıç noktası olarak kullan. Marka DNA'sına ve Adım 5 tasarım kararlarına göre uyarla.

## Belge iskeleti

```html
<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title><!-- ====== EDIT: PAGE TITLE ====== --></title>
  <meta name="description" content="<!-- ====== EDIT: META DESCRIPTION ====== -->" />

  <!-- Open Graph -->
  <meta property="og:title" content="<!-- ====== EDIT: OG TITLE ====== -->" />
  <meta property="og:description" content="<!-- ====== EDIT: OG DESCRIPTION ====== -->" />
  <meta property="og:image" content="REPLACE_WITH_OG_IMAGE_URL" />
  <meta property="og:url" content="REPLACE_WITH_PAGE_URL" />
  <meta property="og:type" content="website" />

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="<!-- ====== EDIT: TWITTER TITLE ====== -->" />
  <meta name="twitter:description" content="<!-- ====== EDIT: TWITTER DESCRIPTION ====== -->" />
  <meta name="twitter:image" content="REPLACE_WITH_OG_IMAGE_URL" />

  <link rel="icon" href="REPLACE_WITH_FAVICON_URL" />

  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DISPLAY_NAME:wght@600;700;800&family=BODY_NAME:wght@400;500;600&display=swap" rel="stylesheet">

  <!-- Tailwind Play CDN. Günlük $50 üzerinde harcamada önceden derlenmiş bir stil sayfasıyla değiştir. -->
  <script src="https://cdn.tailwindcss.com"></script>

  <!-- Marka Tokenları -->
  <style>
    :root {
      --brand-primary: #FROM_BRAND_DNA;
      --brand-accent: #FROM_BRAND_DNA;
      --brand-ink: #FROM_BRAND_DNA;
      --brand-paper: #FROM_BRAND_DNA;
      --brand-muted: #FROM_BRAND_DNA;
    }
    body { font-family: 'Body Name', system-ui, sans-serif; }
    h1, h2, h3 { font-family: 'Display Name', Georgia, serif; }
  </style>

  <!-- Meta Pixel -->
  <!-- ====== EDIT: META PIXEL ID ====== -->
  <script>
    !function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
    fbq('init', 'REPLACE_WITH_YOUR_PIXEL_ID');
    fbq('track', 'PageView');
  </script>
  <noscript><img height="1" width="1" style="display:none" src="https://www.facebook.com/tr?id=REPLACE_WITH_YOUR_PIXEL_ID&ev=PageView&noscript=1"/></noscript>
  <!-- ====== /EDIT ====== -->
</head>

<body class="bg-[var(--brand-paper)] text-[var(--brand-ink)] antialiased">
  <!-- Sections go here -->
</body>
</html>
```

## Kahraman (DTC)

```html
<section class="px-6 md:px-12 pt-8 md:pt-16 pb-16 md:pb-24">
  <div class="max-w-7xl mx-auto">

    <!-- Üst çubuk, bağlantısız logo -->
    <div class="flex justify-between items-center mb-12 md:mb-20">
      <div class="font-bold text-xl">
        <!-- ====== EDIT: BRAND NAME OR LOGO ====== -->
        Brand Name
        <!-- ====== /EDIT ====== -->
      </div>
      <!-- Yalnızca masaüstü nav CTA'sı -->
      <a href="#buy" class="hidden md:inline-block bg-[var(--brand-accent)] text-white px-5 py-2 rounded-md font-semibold">
        <!-- ====== EDIT: NAV CTA ====== -->
        Shop Now
        <!-- ====== /EDIT ====== -->
      </a>
    </div>

    <!-- Kahraman ızgarası -->
    <div class="grid md:grid-cols-12 gap-8 md:gap-12 items-center">
      <div class="md:col-span-7">

        <!-- Üst yazı, güven satırı -->
        <div class="flex items-center gap-2 mb-4 text-sm font-medium tracking-wider uppercase text-[var(--brand-muted)]">
          <!-- ====== EDIT: EYEBROW ====== -->
          ★★★★★ 4.8 from 1,847 reviews
          <!-- ====== /EDIT ====== -->
        </div>

        <h1 class="text-4xl md:text-6xl lg:text-7xl font-bold leading-tight mb-6">
          <!-- ====== EDIT: H1 (MUST MESSAGE MATCH AD) ====== -->
          Sleep deeper in 3 nights. Or get every penny back.
          <!-- ====== /EDIT ====== -->
        </h1>

        <p class="text-lg md:text-xl leading-relaxed text-[var(--brand-ink)]/80 mb-8 max-w-xl">
          <!-- ====== EDIT: SUBHEAD (POLISHED VOC OUTCOME) ====== -->
          Wake up at 6 wide awake, even on the nights you sleep less.
          <!-- ====== /EDIT ====== -->
        </p>

        <a href="#buy" class="inline-block bg-[var(--brand-accent)] text-white px-8 py-4 rounded-md font-semibold text-lg hover:scale-[1.02] transition-transform">
          <!-- ====== EDIT: PRIMARY CTA (PRICE IN BUTTON IF AOV IN AD) ====== -->
          Add to Cart, $48
          <!-- ====== /EDIT ====== -->
        </a>

        <p class="text-sm text-[var(--brand-muted)] mt-3">
          <!-- ====== EDIT: HERO REASSURANCE ====== -->
          Free shipping over $50. 30 day returns.
          <!-- ====== /EDIT ====== -->
        </p>
      </div>

      <div class="md:col-span-5">
        <img src="REPLACE_WITH_PRODUCT_HERO_IMAGE" alt="<!-- ====== EDIT: PRODUCT ALT TEXT ====== -->" class="w-full rounded-lg" loading="eager" />
      </div>
    </div>
  </div>
</section>
```

## Kahraman (Lead Gen, E-posta Yakalama)

```html
<section class="px-6 md:px-12 pt-8 md:pt-16 pb-16 md:pb-24">
  <div class="max-w-7xl mx-auto">

    <div class="flex justify-between items-center mb-12 md:mb-20">
      <div class="font-bold text-xl">Brand Name</div>
    </div>

    <div class="grid md:grid-cols-12 gap-8 md:gap-12 items-center">
      <div class="md:col-span-7">

        <h1 class="text-4xl md:text-6xl lg:text-7xl font-bold leading-tight mb-6">
          <!-- ====== EDIT: H1 (MUST MESSAGE MATCH AD) ====== -->
          The 12 page playbook 8 figure brands use.
          <!-- ====== /EDIT ====== -->
        </h1>

        <p class="text-lg md:text-xl leading-relaxed text-[var(--brand-ink)]/80 mb-8 max-w-xl">
          <!-- ====== EDIT: SUBHEAD ====== -->
          Real frameworks, real client examples, real screenshots. In your inbox in 60 seconds.
          <!-- ====== /EDIT ====== -->
        </p>

        <!-- Tek alanlı form -->
        <form action="REPLACE_WITH_FORM_HANDLER_URL" method="POST" class="flex flex-col sm:flex-row gap-3 max-w-md">
          <input type="email" name="email" required placeholder="your@email.com" class="flex-1 px-4 py-3 rounded-md border-2 border-[var(--brand-muted)]/30 focus:border-[var(--brand-primary)] outline-none text-base" />
          <button type="submit" class="bg-[var(--brand-accent)] text-white px-6 py-3 rounded-md font-semibold whitespace-nowrap">
            <!-- ====== EDIT: SUBMIT BUTTON ====== -->
            Send Me The Playbook
            <!-- ====== /EDIT ====== -->
          </button>
        </form>
        <p class="text-sm text-[var(--brand-muted)] mt-3">Free. 60 seconds. No spam.</p>
      </div>

      <div class="md:col-span-5">
        <img src="REPLACE_WITH_LEAD_MAGNET_COVER" alt="Playbook cover" class="w-full rounded-lg" loading="eager" />
      </div>
    </div>
  </div>
</section>
```

## Sorun pekiştirme

```html
<section class="px-6 md:px-12 py-16 md:py-24 bg-[var(--brand-ink)]/[0.03]">
  <div class="max-w-4xl mx-auto">
    <h2 class="text-3xl md:text-5xl font-bold leading-tight mb-8">
      <!-- ====== EDIT: SECTION H2 ====== -->
      Why everything else stopped working.
      <!-- ====== /EDIT ====== -->
    </h2>

    <!-- Nitelendirmeyle birlikte birebir VOC ağrı alıntısı -->
    <blockquote class="border-l-4 border-[var(--brand-accent)] pl-6 py-2 my-8">
      <p class="text-xl md:text-2xl italic leading-relaxed">
        <!-- ====== EDIT: VERBATIM VOC PAIN QUOTE ====== -->
        "I tried 4 different programs and gained the weight back every time."
        <!-- ====== /EDIT ====== -->
      </p>
      <cite class="block mt-4 text-sm not-italic text-[var(--brand-muted)]">
        <!-- ====== EDIT: ATTRIBUTION ====== -->
        Sarah, 38, Portland
        <!-- ====== /EDIT ====== -->
      </cite>
    </blockquote>

    <p class="text-lg leading-relaxed max-w-2xl">
      <!-- ====== EDIT: AGITATION COPY ====== -->
      Most programs blame your willpower. The science says your willpower was never the problem.
      <!-- ====== /EDIT ====== -->
    </p>
  </div>
</section>
```

## Mekanizma veya Nasıl Çalışır (3 Adım)

```html
<section class="px-6 md:px-12 py-16 md:py-24">
  <div class="max-w-6xl mx-auto">
    <h2 class="text-3xl md:text-5xl font-bold mb-12 md:mb-16 max-w-2xl">
      <!-- ====== EDIT: SECTION H2 ====== -->
      How it works.
      <!-- ====== /EDIT ====== -->
    </h2>

    <div class="grid md:grid-cols-3 gap-8 md:gap-12">
      <div>
        <div class="text-5xl font-bold text-[var(--brand-primary)] mb-4">01</div>
        <h3 class="text-xl font-semibold mb-3">
          <!-- ====== EDIT: STEP 1 HEADING ====== -->
          Take 2 capsules with breakfast.
          <!-- ====== /EDIT ====== -->
        </h3>
        <p class="text-[var(--brand-ink)]/80 leading-relaxed">
          <!-- ====== EDIT: STEP 1 BODY ====== -->
          That's it. No counting. No tracking. No app.
          <!-- ====== /EDIT ====== -->
        </p>
      </div>

      <div>
        <div class="text-5xl font-bold text-[var(--brand-primary)] mb-4">02</div>
        <h3 class="text-xl font-semibold mb-3">
          <!-- ====== EDIT: STEP 2 HEADING ====== -->
          Notice the difference in 7 days.
          <!-- ====== /EDIT ====== -->
        </h3>
        <p class="text-[var(--brand-ink)]/80 leading-relaxed">
          <!-- ====== EDIT: STEP 2 BODY ====== -->
          Most customers report sharper focus and less afternoon crash by day 5.
          <!-- ====== /EDIT ====== -->
        </p>
      </div>

      <div>
        <div class="text-5xl font-bold text-[var(--brand-primary)] mb-4">03</div>
        <h3 class="text-xl font-semibold mb-3">
          <!-- ====== EDIT: STEP 3 HEADING ====== -->
          Reorder when you want.
          <!-- ====== /EDIT ====== -->
        </h3>
        <p class="text-[var(--brand-ink)]/80 leading-relaxed">
          <!-- ====== EDIT: STEP 3 BODY ====== -->
          Cancel anytime. Subscribe and save 15%. Or one off whenever you need.
          <!-- ====== /EDIT ====== -->
        </p>
      </div>
    </div>
  </div>
</section>
```

## Fayda ızgarası

```html
<section class="px-6 md:px-12 py-16 md:py-24 bg-[var(--brand-ink)]/[0.03]">
  <div class="max-w-6xl mx-auto">
    <h2 class="text-3xl md:text-5xl font-bold mb-12 md:mb-16 max-w-2xl">
      <!-- ====== EDIT: SECTION H2 ====== -->
      What changes when you start.
      <!-- ====== /EDIT ====== -->
    </h2>

    <div class="grid md:grid-cols-2 gap-x-12 gap-y-8">
      <div class="border-l-2 border-[var(--brand-accent)] pl-6">
        <!-- ====== EDIT: BENEFIT 1 ====== -->
        <h3 class="text-xl font-semibold mb-2">Sharper focus by 10am</h3>
        <p class="text-[var(--brand-ink)]/80">No more rereading the same paragraph 3 times.</p>
        <!-- ====== /EDIT ====== -->
      </div>
      <div class="border-l-2 border-[var(--brand-accent)] pl-6">
        <!-- ====== EDIT: BENEFIT 2 ====== -->
        <h3 class="text-xl font-semibold mb-2">No 3pm crash</h3>
        <p class="text-[var(--brand-ink)]/80">Steady energy from breakfast through dinner.</p>
        <!-- ====== /EDIT ====== -->
      </div>
      <!-- Toplam 3-6 fayda için tekrarla -->
    </div>
  </div>
</section>
```

## Sosyal kanıt, referanslar

```html
<section class="px-6 md:px-12 py-16 md:py-24">
  <div class="max-w-6xl mx-auto">
    <h2 class="text-3xl md:text-5xl font-bold mb-12 md:mb-16 max-w-2xl">
      <!-- ====== EDIT: SECTION H2 ====== -->
      4,200 customers since 2022.
      <!-- ====== /EDIT ====== -->
    </h2>

    <div class="grid md:grid-cols-3 gap-8">
      <div class="bg-[var(--brand-paper)] border border-[var(--brand-muted)]/20 rounded-lg p-6">
        <div class="text-[var(--brand-accent)] mb-3">★★★★★</div>
        <blockquote class="text-base leading-relaxed mb-6">
          <!-- ====== EDIT: TESTIMONIAL 1 (VERBATIM VOC) ====== -->
          "Took me about a week to notice but my focus is so much better. I used to lose track of what I was reading by paragraph 3."
          <!-- ====== /EDIT ====== -->
        </blockquote>
        <div class="flex items-center gap-3">
          <img src="REPLACE_WITH_CUSTOMER_PHOTO_1" alt="Customer photo" class="w-12 h-12 rounded-full object-cover" />
          <div>
            <!-- ====== EDIT: ATTRIBUTION 1 ====== -->
            <div class="font-semibold text-sm">Marcus, 41</div>
            <div class="text-xs text-[var(--brand-muted)]">Austin, TX</div>
            <!-- ====== /EDIT ====== -->
          </div>
        </div>
      </div>
      <!-- Uzunlukları karıştırarak 2 referans daha için tekrarla -->
    </div>
  </div>
</section>
```

## Karşılaştırma tablosu (DTC)

```html
<section class="px-6 md:px-12 py-16 md:py-24 bg-[var(--brand-ink)]/[0.03]">
  <div class="max-w-5xl mx-auto">
    <h2 class="text-3xl md:text-5xl font-bold mb-12 md:mb-16 max-w-2xl">
      <!-- ====== EDIT: SECTION H2 ====== -->
      How we compare.
      <!-- ====== /EDIT ====== -->
    </h2>

    <div class="overflow-x-auto">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="border-b-2 border-[var(--brand-ink)]">
            <th class="py-4 pr-6 font-semibold"></th>
            <th class="py-4 px-6 font-bold text-[var(--brand-primary)]">
              <!-- ====== EDIT: YOUR BRAND COLUMN HEAD ====== -->
              Your Brand
              <!-- ====== /EDIT ====== -->
            </th>
            <th class="py-4 px-6 font-semibold text-[var(--brand-muted)]">
              <!-- ====== EDIT: ALTERNATIVE COLUMN HEAD ====== -->
              The Drugstore Version
              <!-- ====== /EDIT ====== -->
            </th>
          </tr>
        </thead>
        <tbody>
          <!-- ====== EDIT: COMPARISON ROWS ====== -->
          <tr class="border-b border-[var(--brand-muted)]/20">
            <td class="py-4 pr-6 font-medium">Ingredient quality</td>
            <td class="py-4 px-6">Third party tested, single source</td>
            <td class="py-4 px-6 text-[var(--brand-muted)]">Unknown source, no testing listed</td>
          </tr>
          <tr class="border-b border-[var(--brand-muted)]/20">
            <td class="py-4 pr-6 font-medium">Time to result</td>
            <td class="py-4 px-6">5 to 7 days</td>
            <td class="py-4 px-6 text-[var(--brand-muted)]">Varies, often weeks</td>
          </tr>
          <tr class="border-b border-[var(--brand-muted)]/20">
            <td class="py-4 pr-6 font-medium">Returns</td>
            <td class="py-4 px-6">30 days, full refund, we pay shipping</td>
            <td class="py-4 px-6 text-[var(--brand-muted)]">14 days, unopened only</td>
          </tr>
          <!-- ====== /EDIT ====== -->
        </tbody>
      </table>
    </div>
  </div>
</section>
```

## SSS (JSON-LD şemasıyla birlikte)

```html
<section class="px-6 md:px-12 py-16 md:py-24">
  <div class="max-w-3xl mx-auto">
    <h2 class="text-3xl md:text-5xl font-bold mb-12">
      <!-- ====== EDIT: SECTION H2 ====== -->
      Questions we get a lot.
      <!-- ====== /EDIT ====== -->
    </h2>

    <div class="space-y-4">
      <!-- ====== EDIT: FAQ QUESTIONS (VERBATIM FROM VOC) ====== -->
      <details class="border-b border-[var(--brand-muted)]/20 pb-4 group">
        <summary class="font-semibold text-lg cursor-pointer flex justify-between items-center">
          Does it actually work?
          <span class="text-[var(--brand-muted)] group-open:rotate-45 transition-transform">+</span>
        </summary>
        <p class="mt-3 text-[var(--brand-ink)]/80 leading-relaxed">
          For most customers, yes. We have a 30 day money back guarantee because we know it does not work for everyone.
        </p>
      </details>
      <details class="border-b border-[var(--brand-muted)]/20 pb-4 group">
        <summary class="font-semibold text-lg cursor-pointer flex justify-between items-center">
          How long until I see results?
          <span class="text-[var(--brand-muted)] group-open:rotate-45 transition-transform">+</span>
        </summary>
        <p class="mt-3 text-[var(--brand-ink)]/80 leading-relaxed">
          Most people notice the difference by day 5 to 7. Some take 2 weeks.
        </p>
      </details>
      <!-- ====== /EDIT ====== -->
    </div>
  </div>
</section>

<!-- FAQ Şeması -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Does it actually work?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "For most customers, yes. We have a 30 day money back guarantee because we know it does not work for everyone."
      }
    }
  ]
}
</script>
```

## Garanti bloğu

```html
<section class="px-6 md:px-12 py-16 md:py-24 bg-[var(--brand-primary)]/[0.05]">
  <div class="max-w-3xl mx-auto text-center">
    <h2 class="text-3xl md:text-5xl font-bold mb-6">
      <!-- ====== EDIT: GUARANTEE HEADING ====== -->
      If it does not work, we refund you. Personally.
      <!-- ====== /EDIT ====== -->
    </h2>
    <p class="text-lg leading-relaxed text-[var(--brand-ink)]/80 max-w-2xl mx-auto">
      <!-- ====== EDIT: GUARANTEE COPY ====== -->
      Try the full bag for 30 days. If you don't notice a difference, email mike@brand.com and we refund every cent. We pay return shipping too.
      <!-- ====== /EDIT ====== -->
    </p>
  </div>
</section>
```

## Son CTA

```html
<section id="buy" class="px-6 md:px-12 py-16 md:py-24 bg-[var(--brand-ink)] text-[var(--brand-paper)]">
  <div class="max-w-3xl mx-auto text-center">
    <h2 class="text-3xl md:text-5xl font-bold mb-6">
      <!-- ====== EDIT: FINAL CTA HEADING ====== -->
      Start sleeping deeper tonight.
      <!-- ====== /EDIT ====== -->
    </h2>
    <p class="text-lg leading-relaxed mb-8 opacity-80 max-w-xl mx-auto">
      <!-- ====== EDIT: FINAL CTA SUBHEAD ====== -->
      30 day money back guarantee. Free shipping over $50.
      <!-- ====== /EDIT ====== -->
    </p>
    <a href="REPLACE_WITH_CHECKOUT_URL" class="inline-block bg-[var(--brand-accent)] text-white px-10 py-5 rounded-md font-semibold text-xl hover:scale-[1.02] transition-transform">
      <!-- ====== EDIT: FINAL CTA BUTTON ====== -->
      Add to Cart, $48
      <!-- ====== /EDIT ====== -->
    </a>
  </div>
</section>
```

## Mobil yapışkan CTA çubuğu

```html
<div class="fixed bottom-0 left-0 right-0 bg-[var(--brand-paper)] border-t border-[var(--brand-muted)]/20 p-3 md:hidden z-50 shadow-lg">
  <a href="#buy" class="block w-full text-center bg-[var(--brand-accent)] text-white py-4 rounded-md font-semibold">
    <!-- ====== EDIT: STICKY CTA TEXT ====== -->
    Add to Cart, $48
    <!-- ====== /EDIT ====== -->
  </a>
</div>
```

## Alt bilgi

```html
<footer class="px-6 md:px-12 py-12 border-t border-[var(--brand-muted)]/20">
  <div class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-[var(--brand-muted)]">
    <div>© <span id="year"></span> <!-- ====== EDIT: BRAND NAME ====== -->Brand Name<!-- ====== /EDIT ======--></div>
    <div class="flex gap-6">
      <a href="REPLACE_WITH_PRIVACY_URL" class="hover:text-[var(--brand-ink)]">Privacy</a>
      <a href="REPLACE_WITH_TERMS_URL" class="hover:text-[var(--brand-ink)]">Terms</a>
      <a href="mailto:REPLACE_WITH_SUPPORT_EMAIL" class="hover:text-[var(--brand-ink)]">Contact</a>
    </div>
  </div>
  <script>document.getElementById('year').textContent = new Date().getFullYear();</script>
</footer>
```

## A/B varyant blokları (alttta yorumlanmış)

```html
<!-- ============================================================ -->
<!-- A/B VARIANT BLOCKS                                            -->
<!-- Uncomment the block you want to test, and comment out the     -->
<!-- corresponding live block above. Re deploy to swap.            -->
<!-- ============================================================ -->

<!--
ALT H1 #1 (more direct):
<h1 class="text-4xl md:text-6xl lg:text-7xl font-bold leading-tight mb-6">
  Stop waking up tired. Tonight.
</h1>

ALT H1 #2 (more outcome focused):
<h1 class="text-4xl md:text-6xl lg:text-7xl font-bold leading-tight mb-6">
  Wake up wide awake at 6am. Even on 6 hours of sleep.
</h1>

ALT HERO LAYOUT (centered, no image):
<div class="max-w-3xl mx-auto text-center">
  <h1 class="text-4xl md:text-7xl font-bold mb-6">...</h1>
  <p class="text-xl mb-8">...</p>
  <a href="#buy" class="...">CTA</a>
</div>

ALT SOCIAL PROOF (review stack instead of card grid):
<div class="space-y-8 max-w-2xl mx-auto">
  Single column of full width testimonials
</div>

ALT FINAL CTA MICROCOPY:
"Cancel anytime. We make it one click in your account."
-->
```

## Stripe Satın Al Butonu snippet'i (DTC, isteğe bağlı)

```html
<!-- ====== EDIT: STRIPE BUY BUTTON (OPTIONAL) ====== -->
<stripe-buy-button
  buy-button-id="REPLACE_WITH_BUY_BUTTON_ID"
  publishable-key="REPLACE_WITH_PUBLISHABLE_KEY">
</stripe-buy-button>
<script async src="https://js.stripe.com/v3/buy-button.js"></script>
<!-- ====== /EDIT ====== -->
```

## Shopify Satın Al Butonu snippet'i (DTC, isteğe bağlı)

```html
<!-- ====== EDIT: SHOPIFY BUY BUTTON (OPTIONAL) ====== -->
<div id="product-component-REPLACE_WITH_BUY_BUTTON_ID"></div>
<script>
  // Full Shopify Buy Button SDK initialization.
  // Generate this from Shopify Admin > Sales channels > Buy Button.
</script>
<!-- ====== /EDIT ====== -->
```

## Değişmez kurallar

1. Her bölüm, her düzenlenebilir blokta EDIT işaretleri kullanır.
2. Tüm yer tutucu dizeler `REPLACE_WITH_` önekiyle tüm büyük harfle yazılır.
3. Her `<img>` etiketi gerçek bir src değerine ya da `REPLACE_WITH_` yer tutucusuna sahiptir. `/hero.jpg` gibi kırık yollar asla kullanılmaz.
4. Tüm renkler CSS özel özellikleri kullanır (`var(--brand-primary)` vb.). Tailwind sınıfları içinde tek seferlik hex kodları yoktur.
5. Tüm yazı tipleri bildirilen 2 aileden birini kullanır. `font-sans` veya `font-serif` varsayılanları kullanılmaz.
6. Tüm bölümlerde tutarlı boşluk ölçeği korunur.
7. Her bölüm hiyerarşi için net bir `<h2>` içerir. H1 sayfa başına yalnızca bir kez kullanılır.
8. CTA buton metinlerinde, başlıklarda, gövde kopyasında veya yorumlarda hiçbir yerde tire yoktur. Virgül, "and" veya ayrılmış cümleler kullan.
