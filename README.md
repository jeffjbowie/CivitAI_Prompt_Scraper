# CivitAI Prompt Scraper

Build a reference database of prompts and their resulting image.

Image URLs are in the format of `https://civitai.com/images/{_range}`.  A range of `5000000` to `5634010` was initially chosen.
An infinite `while` loop is created, and begins requesting a random image from the specified range.

If the request's response returns a `200 OK` , `BeautifulSoup` is used to parse the HTML , targeting the `matine-ScrollArea-viewport` class.
We loop through all `<a>` children of this class, and find the anchor tag with a `src` attribute containing the string `original=true` , as this `PNG` file has the generation parameters embedded as EXIF.

After generation parameters are extracted, we modify the URL to re-request the image with a width of `320px` , and store the response as a Base64-encoded BLOB of the original.
As a result, `56,153` images have been acquired, in a DB file of only `2.7 TB`.
