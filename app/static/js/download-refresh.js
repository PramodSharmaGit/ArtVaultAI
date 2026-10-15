// A file download doesn't reload the page, so the "X of 3 free downloads used" text goes stale.
// A moment after a download form is submitted, reload so the page shows the new count
// (or the "all used" message). The page itself is a plain GET, so reloading is safe.
document.querySelectorAll("form[data-download]").forEach(function (form) {
  form.addEventListener("submit", function () {
    setTimeout(function () { window.location.reload(); }, 1200);
  });
});
