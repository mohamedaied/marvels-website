/* Marvels site — shared behaviour.
   The WhatsApp number is read from <meta name="wa-number"> on every page. */
(function () {
  var meta = document.querySelector('meta[name="wa-number"]');
  var WA = meta ? meta.getAttribute('content') : '';
  var lm = document.querySelector('meta[name="leads-url"]');
  var LEADS = lm ? lm.getAttribute('content') : '';
  var isAr = (document.documentElement.getAttribute('lang') || 'ar').indexOf('ar') === 0;

  function waUrl(text) {
    return 'https://wa.me/' + WA + (text ? '?text=' + encodeURIComponent(text) : '');
  }

  // Plain chat links: <a data-wa="optional prefilled text">
  document.querySelectorAll('a[data-wa]').forEach(function (a) {
    a.href = waUrl(a.getAttribute('data-wa'));
    a.target = '_blank';
    a.rel = 'noopener';
  });

  // Mobile menu
  var header = document.querySelector('.site-header');
  var toggle = document.querySelector('.nav-toggle');
  if (header && toggle) {
    toggle.addEventListener('click', function () {
      var open = header.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // Earliest bookable date = today
  document.querySelectorAll('input[type="date"][data-min-today]').forEach(function (el) {
    var d = new Date();
    var iso = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    el.min = iso;
  });

  // Studio estimate: rental hours x hourly rate
  var est = document.querySelector('[data-estimate]');
  if (est) {
    var rate = Number(est.getAttribute('data-rate')) || 0;
    var form = est.closest('form');
    var out = est.querySelector('b');
    var label = est.querySelector('span');
    var update = function () {
      var type = form.querySelector('[name="type"]').value;
      var hours = Number(form.querySelector('[name="hours"]').value) || 0;
      if (type === 'rental') {
        out.textContent = (hours * rate).toLocaleString('en-US') + (isAr ? ' جنيه' : ' EGP');
        label.textContent = isAr ? 'التكلفة التقديرية لإيجار الاستوديو' : 'Estimated studio rental';
      } else {
        out.textContent = isAr ? 'حسب الباقة' : 'Quoted per package';
        label.textContent = isAr ? 'هنأكدلك السعر على واتساب' : 'We confirm the price on WhatsApp';
      }
    };
    form.addEventListener('input', update);
    form.addEventListener('change', update);
    update();
  }

  // Forms that turn into a WhatsApp message
  document.querySelectorAll('form[data-wa-form]').forEach(function (form) {
    var result = form.parentElement.querySelector('.result');
    form.addEventListener('input', function () { form.removeAttribute('data-sent'); });
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      form.classList.add('tried');
      if (!form.reportValidity()) return;
      var lines = [form.getAttribute('data-wa-form')];
      form.querySelectorAll('[data-label]').forEach(function (el) {
        var v = el.tagName === 'SELECT' ? el.options[el.selectedIndex].text : el.value.trim();
        if (v) lines.push(el.getAttribute('data-label') + ': ' + v);
      });
      var est = form.querySelector('[data-estimate] b');
      if (est && form.querySelector('[name="type"]').value === 'rental') {
        lines.push((isAr ? 'التكلفة التقديرية' : 'Estimate') + ': ' + est.textContent);
      }
      if (LEADS && !form.getAttribute('data-sent')) {
        var hp = form.querySelector('[name="website_hp"]');
        if (!(hp && hp.value)) {
          var data = new URLSearchParams();
          data.append('form', form.getAttribute('data-wa-form'));
          data.append('lang', isAr ? 'ar' : 'en');
          data.append('page', location.pathname);
          form.querySelectorAll('[name]').forEach(function (el) {
            if (el.name === 'website_hp') return;
            var v = el.tagName === 'SELECT' ? el.options[el.selectedIndex].text : el.value.trim();
            if (v) data.append('f_' + el.name, v);
          });
          try { fetch(LEADS, { method: 'POST', mode: 'no-cors', body: data, keepalive: true }); } catch (err) {}
          form.setAttribute('data-sent', '1');
        }
      }
      var text = lines.join('\n');
      var url = waUrl(text);
      if (result) {
        result.hidden = false;
        result.querySelector('pre').textContent = text;
        var go = result.querySelector('a.go');
        go.href = url;
        result.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        var copy = result.querySelector('button.copy');
        if (copy) {
          copy.onclick = function () {
            var done = function () { copy.textContent = isAr ? 'اتنسخت' : 'Copied'; };
            if (navigator.clipboard && navigator.clipboard.writeText) {
              navigator.clipboard.writeText(text).then(done, function () { selectPre(result); });
            } else { selectPre(result); }
          };
        }
      }
      try { window.open(url, '_blank', 'noopener'); } catch (err) { /* the link in the panel still works */ }
    });
  });

  function selectPre(result) {
    var pre = result.querySelector('pre');
    var range = document.createRange();
    range.selectNodeContents(pre);
    var sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
  }
})();
