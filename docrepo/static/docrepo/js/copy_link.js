/*
 * Copy buttons for document links.
 *
 *   <button type="button" data-docrepo-copy="#some_input_or_textarea">Copy</button>
 *
 * Clicking copies the target field's value and the button reads "Copied".
 * The handler is delegated from document, so buttons in HTML loaded later
 * (the Copy Links bulk-action modal) work without their own script.
 */
(function ($) {
  if (window.DocRepoCopyLink) return;

  function fallbackCopy(field) {
    field.select();
    try { return document.execCommand('copy'); } catch (e) { return false; }
  }

  function copy(field, done) {
    var text = field.value;
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done, function () {
        if (fallbackCopy(field)) done();
      });
    } else if (fallbackCopy(field)) {
      done();
    }
  }

  $(document).on('click', '[data-docrepo-copy]', function () {
    var button = this;
    var field = document.querySelector(button.getAttribute('data-docrepo-copy'));
    if (!field) return;
    copy(field, function () {
      var label = button.getAttribute('data-copied-label') || 'Copied';
      if (!button.hasAttribute('data-label')) button.setAttribute('data-label', button.textContent);
      button.textContent = label;
      setTimeout(function () { button.textContent = button.getAttribute('data-label'); }, 2000);
    });
  });

  window.DocRepoCopyLink = { copy: copy };
})(window.jQuery);
