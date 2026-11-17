# Tailwind (precompiled)

`static/css/tailwind.css` replaces the runtime CDN (`cdn.tailwindcss.com`) so the browser no longer downloads and
JIT-compiles Tailwind on every page load.

Rebuild after adding new Tailwind classes to `templates/index.html` or `static/js/*.js`:

    cd webai/tools/tailwind
    npx tailwindcss@3.4.16 -c tailwind.config.js -i input.css -o ../../static/css/tailwind.css --minify

Then bump `?v=` of the `tailwind.css` link in `templates/index.html`.

Rollback to the CDN: in `templates/index.html` remove the `tailwind.css` link and re-add
`<script src="https://cdn.tailwindcss.com/3.4.16"></script>` plus the inline `tailwind.config = {...}` block.
