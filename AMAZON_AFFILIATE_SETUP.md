# NUSKHALO Amazon.in Affiliate Video Workflow

## Current safe mode
- Generates one original Hindi 9:16 product-video draft from a manually curated product entry.
- Stores the MP4 and a text description as a GitHub Actions artifact.
- Does not scrape Amazon, copy Amazon product photos, or publish anything.
- You must review every product claim, link, narration and video before publishing.

## Add a product
Edit `amazon_products.json` and add an entry to `products`:
- `asin`: Amazon product ASIN
- `name_hi`: original Hindi product title
- `original_summary_hi`: your own short summary
- `original_features_hi`: 1–3 facts rewritten in your own words after checking the live listing
- `hindi_narration`: original Hindi voiceover
- `affiliate_url`: your own Amazon Associates Special Link (not a normal product URL)

Do not scrape Amazon pages. Do not copy Amazon product images, reviews, ratings, star scores, seller claims or descriptions into the video. Use original graphics or footage you have rights to use. Do not state a price unless the required Amazon API terms permit it and it is refreshed correctly; the draft template deliberately avoids a price.

## Amazon account requirements
Apply to Amazon.in Associates and list the exact public social profile URLs you intend to use. Amazon's current review guidance says at least three qualifying sales are required within 180 days; accepted social pages generally need substantial organic followers (often 500+) and at least 10 original public posts. Personal orders do not qualify.

Amazon's current Creators API documentation lists a separate access threshold of 10 qualifying sales in the past 30 days, plus Associates enrollment and API registration. Until you have eligible API access, enter only original manually reviewed facts and your own Associates Special Link.

Required account-level disclosure:
`As an Amazon Associate I earn from qualifying purchases.`
Put a clear disclosure near every affiliate link, such as `#ad` or `(paid link)`.

## Publishing
This workflow only creates artifacts. YouTube private upload requires valid channel OAuth credentials and a separate explicitly enabled uploader. Facebook Reels publishing also requires a Meta Page/app and supported permissions; this workflow does not publish to Facebook. No content is made public by this workflow.

## Run
Open GitHub → Actions → **NUSKHALO Amazon Affiliate Product Video Drafts** → Run workflow. The first run stops with `NO_PRODUCTS` until a real reviewed product and your Associates Special Link are entered.
