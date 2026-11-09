/*
 * Copied from highschool_admin (staticfiles/highschool_admin/js/file_dropzone.js,
 * v0.0.33) so docrepo does not depend on that package. Both copies share the
 * window.HSDropzone guard, so loading both on one page is harmless.
 *
 * Drag-and-drop for file inputs.
 *
 * Mark an <input type="file"> with data-dropzone and it is wrapped in a drop
 * target. The input itself is kept (visually hidden, still focusable), so a
 * dropped file lands in input.files and form posts / page scripts that read
 * the input work unchanged.
 *
 * Options, as data attributes on the input:
 *   data-dropzone-extensions=".csv"   accepted extensions (comma-separated);
 *                                     omit to accept any file
 *   data-dropzone-prompt="..."        text shown before a file is chosen
 *   data-dropzone-compact             small variant for table rows
 *   data-dropzone-submit="selector"   a button in the same form that stays
 *                                     disabled until a file is chosen
 *
 * A page script that clears the input should dispatch a 'change' event on it
 * afterwards so the zone resets.
 */
(function () {
  if (window.HSDropzone) return;

  var CSS = [
    '.hs-dropzone{display:block;text-align:center;cursor:pointer;margin-bottom:.5rem;',
    'padding:2rem 1rem;border:2px dashed #adb5bd;border-radius:.5rem;background:#f8f9fa;',
    'transition:background .15s,border-color .15s;font-weight:normal}',
    '.hs-dropzone.is-compact{padding:.5rem .75rem;margin-bottom:0;min-width:12rem;font-size:.875rem}',
    '.hs-dropzone:hover,.hs-dropzone.is-dragover{border-color:#007bff;background:#e9f2ff}',
    '.hs-dropzone.has-file{border-style:solid;border-color:#28a745;background:#eef9f1}',
    '.hs-dropzone:has(input:focus-visible){outline:2px solid #007bff;outline-offset:2px}',
    '.hs-dropzone-name{font-weight:600;word-break:break-all}'
  ].join('');

  function injectCss() {
    if (document.getElementById('hs-dropzone-css')) return;
    var style = document.createElement('style');
    style.id = 'hs-dropzone-css';
    style.textContent = CSS;
    document.head.appendChild(style);
  }

  function extensionsOf(input) {
    var raw = input.getAttribute('data-dropzone-extensions');
    if (!raw) return [];
    return raw.split(',').map(function (e) { return e.trim().toLowerCase(); })
      .filter(Boolean);
  }

  function attach(input) {
    if (!input || input.dataset.dropzoneReady) return;
    input.dataset.dropzoneReady = '1';
    injectCss();

    var compact = input.hasAttribute('data-dropzone-compact');
    var extensions = extensionsOf(input);
    var kind = extensions.length === 1 ? extensions[0].replace('.', '').toUpperCase() + ' ' : '';
    var promptText = input.getAttribute('data-dropzone-prompt') ||
      (compact ? 'Drop a file or click' : 'Drag your ' + kind + 'file here');

    if (!input.id) input.id = 'hs-dropzone-' + Math.random().toString(36).slice(2);

    var zone = document.createElement('label');
    zone.className = 'hs-dropzone' + (compact ? ' is-compact' : '');
    zone.setAttribute('for', input.id);
    input.parentNode.insertBefore(zone, input);
    zone.appendChild(input);
    input.classList.add('sr-only');

    var prompt = document.createElement('div');
    if (compact) {
      prompt.innerHTML = '<i class="fas fa-file-upload text-muted mr-1" aria-hidden="true"></i>';
      prompt.appendChild(document.createTextNode(promptText));
    } else {
      prompt.innerHTML = '<i class="fas fa-file-upload fa-2x mb-2 text-muted d-block" aria-hidden="true"></i>' +
        '<strong></strong> or <span class="text-primary">click to choose one</span>';
      prompt.querySelector('strong').textContent = promptText;
    }
    var nameEl = document.createElement('div');
    nameEl.className = 'hs-dropzone-name d-none';
    zone.appendChild(prompt);
    zone.appendChild(nameEl);

    var errorEl = document.createElement('div');
    errorEl.className = 'small text-danger d-none';
    errorEl.setAttribute('role', 'alert');
    zone.parentNode.insertBefore(errorEl, zone.nextSibling);

    function submitButton() {
      var selector = input.getAttribute('data-dropzone-submit');
      return selector && input.form ? input.form.querySelector(selector) : null;
    }

    function accepted(file) {
      if (!extensions.length) return true;
      var name = file.name.toLowerCase();
      return extensions.some(function (ext) { return name.slice(-ext.length) === ext; });
    }

    function showError(message) {
      errorEl.textContent = message;
      errorEl.classList.toggle('d-none', !message);
    }

    function refresh() {
      var file = input.files && input.files[0];
      var ok = !!file && accepted(file);
      if (file && !ok) {
        showError('"' + file.name + '" is not a ' + extensions.join(' or ') +
          ' file.' + (extensions.indexOf('.csv') !== -1 ? ' Save the spreadsheet as CSV and try again.' : ''));
        input.value = '';
      } else {
        showError('');
      }
      zone.classList.toggle('has-file', ok);
      prompt.classList.toggle('d-none', ok);
      nameEl.classList.toggle('d-none', !ok);
      nameEl.textContent = ok ? file.name + (compact ? '' : ' — click or drop to replace') : '';
      var submit = submitButton();
      if (submit) submit.disabled = !ok;
    }

    input.addEventListener('change', refresh);

    ['dragenter', 'dragover'].forEach(function (type) {
      zone.addEventListener(type, function (e) {
        e.preventDefault();
        zone.classList.add('is-dragover');
      });
    });
    ['dragleave', 'dragend', 'drop'].forEach(function (type) {
      zone.addEventListener(type, function () { zone.classList.remove('is-dragover'); });
    });
    zone.addEventListener('drop', function (e) {
      e.preventDefault();
      var files = e.dataTransfer && e.dataTransfer.files;
      if (!files || !files.length) return;
      if (files.length > 1 && !input.multiple) {
        showError('Drop one file at a time.');
        return;
      }
      input.files = files;
      input.dispatchEvent(new Event('change', { bubbles: true }));
    });

    refresh();
  }

  function attachAll(root) {
    (root || document).querySelectorAll('input[type=file][data-dropzone]').forEach(attach);
  }

  // A file dropped outside a zone would otherwise open in the browser and
  // leave the page (losing anything typed). Only file drags are stopped, so
  // dragging text into a field still works, and a plain file input keeps its
  // own native drop.
  function isFileDrag(e) {
    var types = e.dataTransfer && e.dataTransfer.types;
    return !!types && Array.prototype.indexOf.call(types, 'Files') !== -1;
  }
  ['dragover', 'drop'].forEach(function (type) {
    window.addEventListener(type, function (e) {
      if (!isFileDrag(e)) return;
      var t = e.target;
      if (t.closest && (t.closest('.hs-dropzone') || t.closest('input[type=file]'))) return;
      e.preventDefault();
    });
  });

  window.HSDropzone = { attach: attach, attachAll: attachAll };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { attachAll(); });
  } else {
    attachAll();
  }
})();
