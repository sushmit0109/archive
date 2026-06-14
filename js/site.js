'use strict';

/* ================================================================
   Bangladesh Reform Commission – static site app
   Vanilla JS SPA using hash routing + Fetch API
================================================================ */

const App = (() => {

  // ── PDF hosting base URL ───────────────────────────────────────
  // Change this one line to point PDFs anywhere (local, GitHub Releases, CDN…)
  const PDF_BASE = './pdfs/attachment/';

  function pdfUrl(filename) { return filename ? PDF_BASE + filename : ''; }

  // ── state ──────────────────────────────────────────────────────
  let _lang      = 'bn';
  let _books     = [];
  let _i18n      = { bn: {}, en: {} };
  let _secCache  = {};   // section.id → section object (paragraphs included)
  let _fetchCache = {}; // url → parsed JSON (avoid re-fetching same data)
  let _curPage   = 1;   // current notice page

  async function cachedFetch(url) {
    if (_fetchCache[url]) return _fetchCache[url];
    const data = await fetch(url).then(r => r.json());
    _fetchCache[url] = data;
    return data;
  }

  // ── translation helpers ────────────────────────────────────────
  function t(path) {
    const keys = path.split('.');
    let node = (_i18n[_lang] || {}).global;
    for (const k of keys) { if (node == null) return ''; node = node[k]; }
    return node || '';
  }

  function bookName(b)   { return _lang === 'bn' ? (b.nameBangla || b.name)   : (b.name || b.nameBangla);   }
  function noticeName(n) { return _lang === 'bn' ? (n.titleBangla || n.title) : (n.title || n.titleBangla); }

  // ── router ─────────────────────────────────────────────────────
  function getRoute() {
    const hash  = (location.hash || '#/').replace(/^#\/?/, '');
    const parts = hash.split('/');
    return { page: parts[0] || 'home', id: parts[1] || null };
  }

  async function router() {
    // _secCache is populated per-commission; _fetchCache persists across all navigation
    const { page, id } = getRoute();
    window.scrollTo(0, 0);
    updateNavActive(page);
    switch (page) {
      case '':
      case 'home':      await renderHome();              break;
      case 'view':      if (id) await renderReport(id);
                        else    await renderHome();       break;
      case 'summary':   renderSummary();                 break;
      case 'notice':    id ? await renderNoticeDetail(id)
                           : await renderNotice(1);      break;
      case 'gallery':   renderGallery();                 break;
      default:          await renderHome();
    }
  }

  function updateNavActive(page) {
    document.querySelectorAll('.site-nav a[id^="nav-"]').forEach(a => a.classList.remove('active'));
    const map = { home: 'nav-home', '': 'nav-home', commission: 'nav-commission',
                  view: 'nav-commission', summary: 'nav-summary',
                  notice: 'nav-notice', gallery: 'nav-gallery' };
    const el = document.getElementById(map[page]);
    if (el) el.classList.add('active');
  }

  async function ensureLang(lang) {
    if (_i18n[lang] && _i18n[lang].global) return;
    const d = await cachedFetch(`./i18n/${lang}/global.json`).catch(() => ({}));
    _i18n[lang] = d;
  }

  // ── init ───────────────────────────────────────────────────────
  async function init() {
    document.getElementById('footer-year').textContent = new Date().getFullYear();

    // only load the default language (bn) and books on startup; en loads on first toggle
    await Promise.all([
      ensureLang('bn'),
      cachedFetch('./api-data/books.json').then(d => { _books = d; }).catch(() => {})
    ]);

    window.addEventListener('hashchange', router);
    await router();
  }

  // ── language ───────────────────────────────────────────────────
  async function toggleLang() {
    _lang = document.getElementById('lang-check').checked ? 'en' : 'bn';
    await ensureLang(_lang);  // lazy-load the other language only on first switch
    router();
  }

  // ── helpers ────────────────────────────────────────────────────
  function app()    { return document.getElementById('app'); }
  function spinner() { return `<div class="spinner-wrap"><i class="fas fa-spinner fa-spin fa-2x"></i></div>`; }

  function pdfLink(filename, label, cls = 'btn btn-sm btn-outline-primary') {
    if (!filename) return '';
    return `<a href="${pdfUrl(filename)}" target="_blank" class="${cls}"><i class="fas fa-download"></i> ${label}</a>`;
  }

  // ── HOME ───────────────────────────────────────────────────────
  async function renderHome() {
    const speech = t('landingPage.speech') || '';
    const heading = t('landingPage.heading') || 'মাননীয় প্রধান উপদেষ্টা মহোদয়ের ভূমিকা';
    const mainTitle = t('landingPage.mainTitle') || 'বাংলাদেশ সরকার কর্তৃক গঠিত সংস্কার কমিশনসমূহের প্রতিবেদন';
    const chiefAdvisor = t('landingPage.chiefAdvisor') || '~ ড. মুহাম্মদ ইউনূস, মাননীয় প্রধান উপদেষ্টা';

    app().innerHTML = `
      <div style="max-width:1140px; margin:0 auto;">
        <div class="mb-3" style="border-radius:12px; overflow:hidden;">
          <img src="./images/july-revolution.jpg" alt="July Revolution" class="hero-img" fetchpriority="high">
        </div>

        <h2 class="section-heading">${heading}</h2>

        <div class="speech-box mb-4">
          <p style="margin:0;">${speech}</p>
          <div class="text-end mt-3" style="font-weight:700; font-size:0.9rem;">
            ${chiefAdvisor}
          </div>
        </div>

        <h2 class="section-heading" id="commission">${mainTitle}</h2>

        <div class="row g-3" id="commission-grid">
          ${spinner()}
        </div>
      </div>`;

    renderCommissionGrid();
  }

  function renderCommissionGrid() {
    const grid = document.getElementById('commission-grid');
    if (!grid) return;
    if (!_books.length) { grid.innerHTML = '<p class="text-muted p-3">ডেটা লোড হয়নি।</p>'; return; }

    const sorted = [..._books].sort((a, b) => a.serial - b.serial);
    grid.innerHTML = sorted.map(book => `
      <div class="col-12 col-sm-6 col-xl-4">
        <a href="#/view/${book.id}" class="commission-card">
          <img src="./images/BDGov.jpg" alt="" loading="lazy">
          <div class="c-name">${bookName(book)}</div>
          <span class="c-btn" aria-hidden="true">›</span>
        </a>
      </div>`).join('');
  }

  // ── COMMISSION REPORT ──────────────────────────────────────────
  async function renderReport(id) {
    const book = _books.find(b => b.id == id);
    if (!book) { app().innerHTML = '<p class="p-4">Commission not found.</p>'; return; }

    const title    = bookName(book);
    const dlReport = pdfLink(book.pdfName, (_lang === 'bn' ? 'প্রতিবেদন' : 'Report'));
    const dlSumBn  = pdfLink(book.summaryFileName, 'সারসংক্ষেপ (বাংলা)');
    const dlSumEn  = pdfLink(book.summaryEn, 'Summary (English)');

    const commSelect = [..._books].sort((a, b) => a.serial - b.serial).map(b =>
      `<option value="${b.id}"${b.id == id ? ' selected' : ''}>${bookName(b)}</option>`
    ).join('');

    app().innerHTML = `
      <div style="max-width:1280px; margin:0 auto;">
        <!-- top bar -->
        <div class="d-flex justify-content-between align-items-start flex-wrap gap-2 mb-3">
          <div>
            <h4 style="color:var(--primary); margin:0 0 0.4rem;">${title}</h4>
            <div class="d-flex flex-wrap gap-2">${dlReport}${dlSumBn}${dlSumEn}</div>
          </div>
          <a href="#/" class="btn btn-sm btn-secondary mt-1"><i class="fas fa-arrow-left"></i> ফিরে যান</a>
        </div>

        <div class="row g-3">
          <!-- sidebar -->
          <div class="col-md-4 col-lg-3">
            <div class="sidebar-panel">
              <div class="mb-2">
                <label style="font-size:0.8rem; color:#555; font-weight:600;">অন্যান্য কমিশন</label>
                <select class="form-select form-select-sm mt-1" onchange="location.hash='#/view/'+this.value">
                  ${commSelect}
                </select>
              </div>
              <hr style="margin:0.6rem 0;">
              <div id="chapter-tree">${spinner()}</div>
            </div>
          </div>

          <!-- content -->
          <div class="col-md-8 col-lg-9">
            <div class="content-panel" id="content-area">
              <div class="placeholder-msg">
                <i class="fas fa-hand-point-left fa-2x mb-3" style="color:#ccc;"></i>
                <p>${_lang === 'bn' ? 'বাম দিক থেকে একটি অধ্যায় নির্বাচন করুন' : 'Select a chapter from the left panel'}</p>
              </div>
            </div>
          </div>
        </div>
      </div>`;

    if (book.hasVolume) {
      await loadVolumeWise(id);
    } else {
      await loadChapters(id);
    }
  }

  async function loadChapters(id) {
    const treeEl = document.getElementById('chapter-tree');
    try {
      const chapters = await cachedFetch(`./api-data/chapters-commission-${id}.json`);
      chapters.forEach(ch => (ch.sections || []).forEach(s => { _secCache[s.id] = s; }));
      const sorted = [...chapters].sort((a, b) => (a.serial - b.serial) || (a.id - b.id));
      treeEl.innerHTML = `<ul class="tree-list">${sorted.map(buildChapterNode).join('')}</ul>`;
      attachTreeEvents(treeEl);
    } catch {
      treeEl.innerHTML = '<p class="text-danger small p-2">ডেটা লোড হয়নি</p>';
    }
  }

  async function loadVolumeWise(id) {
    const treeEl = document.getElementById('chapter-tree');
    try {
      const volumes = await cachedFetch(`./api-data/volume-wise-commission-${id}.json`);
      volumes.forEach(vol => (vol.chapters || []).forEach(ch =>
        (ch.sections || []).forEach(s => { _secCache[s.id] = s; })
      ));
      const sorted = [...volumes].sort((a, b) => (a.serial - b.serial) || (a.id - b.id));
      treeEl.innerHTML = `<ul class="tree-list">${sorted.map(buildVolumeNode).join('')}</ul>`;
      attachTreeEvents(treeEl);
    } catch {
      treeEl.innerHTML = '<p class="text-danger small p-2">ডেটা লোড হয়নি</p>';
    }
  }

  function buildVolumeNode(vol) {
    const chapters = [...(vol.chapters || [])].sort((a, b) => (a.serial - b.serial) || (a.id - b.id));
    const dlBtn = vol.fileName
      ? `<a href="${pdfUrl(vol.fileName)}" target="_blank" style="margin-left:auto; color:var(--accent); font-size:0.8rem;"><i class="fas fa-download"></i></a>`
      : '';
    return `
      <li class="tree-item">
        <div class="tree-label vol-label tree-toggle" data-target="vol-${vol.id}">
          <i class="fas fa-chevron-right toggle-icon"></i>
          <span style="flex:1;">${vol.nameBangla || vol.name || ''}</span>
          ${dlBtn}
        </div>
        <ul class="tree-list tree-children" id="vol-${vol.id}">
          ${chapters.map(buildChapterNode).join('')}
        </ul>
      </li>`;
  }

  function buildChapterNode(ch) {
    const sections = [...(ch.sections || [])].sort((a, b) => (a.serial - b.serial) || (a.id - b.id));
    const hasChildren = sections.length > 0;
    return `
      <li class="tree-item">
        <div class="tree-label ${hasChildren ? 'tree-toggle' : 'tree-section'}"
             data-target="${hasChildren ? 'ch-' + ch.id : ''}"
             data-chid="${ch.id}"
             data-title="${escAttr(ch.title || ch.chapterName || '')}">
          ${hasChildren ? `<i class="fas fa-chevron-right toggle-icon"></i>` : `<i class="fas fa-minus" style="font-size:0.6rem; color:#aaa; width:12px;"></i>`}
          <span>${ch.title || ch.chapterName || ''}</span>
        </div>
        ${hasChildren ? `<ul class="tree-list tree-children" id="ch-${ch.id}">${sections.map(buildSectionNode).join('')}</ul>` : ''}
      </li>`;
  }

  function buildSectionNode(sec) {
    const isPdf = sec.hasPdf && sec.pdfName;
    return `
      <li class="tree-item">
        <div class="tree-label sec-label tree-section"
             data-secid="${sec.id}"
             data-secpdf="${isPdf ? sec.pdfName : ''}"
             data-title="${escAttr(sec.name || '')}">
          <i class="fas fa-file${isPdf ? '-pdf' : '-alt'}" style="font-size:0.75rem; color:#999; width:12px;"></i>
          <span>${sec.name || ''}</span>
        </div>
      </li>`;
  }

  function attachTreeEvents(container) {
    container.querySelectorAll('.tree-toggle').forEach(el => {
      el.addEventListener('click', () => {
        const targetId = el.dataset.target;
        if (!targetId) return;
        const child = document.getElementById(targetId);
        if (child) {
          const isOpen = child.classList.toggle('open');
          el.classList.toggle('open', isOpen);
        }
      });
    });

    container.querySelectorAll('.tree-section').forEach(el => {
      el.addEventListener('click', (e) => {
        e.stopPropagation();
        document.querySelectorAll('.tree-label.active').forEach(a => a.classList.remove('active'));
        el.classList.add('active');

        const pdfName = el.dataset.secpdf;
        const title   = el.dataset.title || el.textContent.trim();

        if (pdfName) {
          showPdfContent(title, pdfName);
        } else if (el.dataset.secid) {
          showSectionContent(title, parseInt(el.dataset.secid, 10));
        } else if (el.dataset.chid) {
          showChapterPlaceholder(title);
        }
      });
    });
  }

  function showChapterPlaceholder(title) {
    document.getElementById('content-area').innerHTML = `
      <h5 class="content-heading">${title}</h5>
      <p class="text-muted small">${_lang === 'bn' ? 'একটি বিভাগ নির্বাচন করুন' : 'Select a section below'}</p>`;
  }

  function showSectionContent(title, secId) {
    const sec = _secCache[secId];
    const area = document.getElementById('content-area');
    if (!sec) { area.innerHTML = `<h5 class="content-heading">${title}</h5><p class="text-muted">বিষয়বস্তু পাওয়া যায়নি।</p>`; return; }

    const paragraphs = [...(sec.paragraphs || [])].sort((a, b) => (a.serial - b.serial) || (a.id - b.id));
    area.innerHTML = `
      <h5 class="content-heading">${title}</h5>
      ${paragraphs.map(p => `
        <div class="paragraph-block">
          ${p.header ? `<div class="para-header">${p.header}</div>` : ''}
          <div class="para-body">
            ${p.indexChar ? `<span class="para-index">${p.indexChar}</span>` : ''}
            <span>${p.content ? p.content.replace(/\n/g, '<br>') : ''}</span>
          </div>
          ${p.hasImage && p.fileName ? `<img src="${pdfUrl(p.fileName)}" style="max-width:100%; margin-top:0.5rem; border-radius:4px;">` : ''}
        </div>`).join('')}`;
  }

  function showPdfContent(title, pdfName) {
    const url = pdfUrl(pdfName);
    document.getElementById('content-area').innerHTML = `
      <h5 class="content-heading">${title}</h5>
      <div class="d-flex gap-2 mb-3 flex-wrap">
        <a href="${url}" target="_blank" class="btn btn-primary btn-sm"><i class="fas fa-external-link-alt me-1"></i>${_lang === 'bn' ? 'নতুন ট্যাবে খুলুন' : 'Open in new tab'}</a>
        <a href="${url}" download class="btn btn-outline-secondary btn-sm"><i class="fas fa-download me-1"></i>${_lang === 'bn' ? 'ডাউনলোড করুন' : 'Download'}</a>
      </div>
      <object data="${url}" type="application/pdf" class="pdf-frame">
        <p style="color:#888; text-align:center; padding:2rem;">
          ${_lang === 'bn' ? 'পিডিএফ প্রিভিউ সাপোর্ট করে না।' : 'PDF preview not supported in this browser.'}
          <br><a href="${url}" target="_blank">${_lang === 'bn' ? 'এখানে ক্লিক করুন' : 'Click here to open'}</a>
        </p>
      </object>`;
  }

  // ── SUMMARY ────────────────────────────────────────────────────
  function renderSummary() {
    const sorted = [..._books].sort((a, b) => a.serial - b.serial);
    app().innerHTML = `
      <div style="max-width:960px; margin:0 auto;">
        <div class="content-panel">
          <h4 class="content-heading">প্রতিবেদনের সারসংক্ষেপ</h4>
          <div class="table-responsive">
            <table class="table table-bordered table-striped data-table">
              <thead>
                <tr>
                  <th style="width:5%">ক্রম</th>
                  <th>কমিশনের নাম</th>
                  <th class="text-center" style="width:20%">সারসংক্ষেপ (বাংলা)</th>
                  <th class="text-center" style="width:20%">Summary (English)</th>
                </tr>
              </thead>
              <tbody>
                ${sorted.map((book, i) => `
                  <tr>
                    <td>${i + 1}</td>
                    <td>${bookName(book)}</td>
                    <td class="text-center">
                      ${book.summaryFileName
                        ? `<a href="${pdfUrl(book.summaryFileName)}" target="_blank"><i class="fas fa-download me-1"></i>ডাউনলোড</a>`
                        : '—'}
                    </td>
                    <td class="text-center">
                      ${book.summaryEn
                        ? `<a href="${pdfUrl(book.summaryEn)}" target="_blank"><i class="fas fa-download me-1"></i>Download</a>`
                        : '—'}
                    </td>
                  </tr>`).join('')}
              </tbody>
            </table>
          </div>
        </div>
      </div>`;
  }

  // ── NOTICE LIST ────────────────────────────────────────────────
  async function renderNotice(pageNum) {
    _curPage = pageNum;
    app().innerHTML = `<div style="max-width:1040px;margin:0 auto;">${spinner()}</div>`;
    try {
      const data    = await cachedFetch(`./api-data/notices-page${pageNum}.json`);
      const notices = [...(data.content || [])].sort((a, b) => b.serial - a.serial || b.id - a.id);
      const total   = data.totalPages || 1;

      app().innerHTML = `
        <div style="max-width:1040px; margin:0 auto;">
          <div class="content-panel">
            <h4 class="content-heading">নোটিশ বোর্ড</h4>
            <div class="table-responsive">
              <table class="table table-bordered table-striped data-table">
                <thead>
                  <tr>
                    <th style="width:5%">ক্রম</th>
                    <th>শিরোনাম</th>
                    <th class="text-center" style="width:18%">তারিখ</th>
                    <th class="text-center" style="width:8%">ডাউনলোড</th>
                  </tr>
                </thead>
                <tbody>
                  ${notices.map((n, i) => `
                    <tr>
                      <td>${(pageNum - 1) * 10 + i + 1}</td>
                      <td>
                        <a href="#/notice/${n.id}" style="color:var(--primary);">${noticeName(n)}</a>
                      </td>
                      <td class="text-center">${n.publishDate || ''}</td>
                      <td class="text-center">
                        ${n.pdfUrl ? `<a href="${pdfUrl(n.pdfUrl)}" target="_blank"><img src="./images/pdf.png" width="26" alt="PDF"></a>` : ''}
                      </td>
                    </tr>`).join('')}
                </tbody>
              </table>
            </div>
            <div class="d-flex justify-content-center align-items-center gap-2 mt-3">
              ${pageNum > 1 ? `<button class="page-btn" onclick="App.goNoticePage(${pageNum - 1})">«&nbsp;আগের পাতা</button>` : ''}
              <span class="page-btn current">${pageNum} / ${total}</span>
              ${pageNum < total ? `<button class="page-btn" onclick="App.goNoticePage(${pageNum + 1})">পরের পাতা&nbsp;»</button>` : ''}
            </div>
          </div>
        </div>`;
    } catch {
      app().innerHTML = '<p class="text-danger p-4">নোটিশ লোড হয়নি।</p>';
    }
  }

  async function goNoticePage(p) { await renderNotice(p); }

  // ── NOTICE DETAIL ──────────────────────────────────────────────
  async function renderNoticeDetail(id) {
    app().innerHTML = `<div style="max-width:820px;margin:0 auto;">${spinner()}</div>`;
    let notice = null;
    for (let p = 1; p <= 2 && !notice; p++) {
      try {
        const data = await cachedFetch(`./api-data/notices-page${p}.json`);
        notice = (data.content || []).find(n => n.id == id);
      } catch {}
    }
    if (!notice) { app().innerHTML = '<p class="p-4">নোটিশ পাওয়া যায়নি।</p>'; return; }

    app().innerHTML = `
      <div style="max-width:820px; margin:0 auto;">
        <div class="content-panel">
          <div class="d-flex justify-content-end mb-3">
            <a href="#/notice" class="btn btn-sm btn-secondary"><i class="fas fa-arrow-left me-1"></i>নোটিশ তালিকা</a>
          </div>
          <h4 style="color:var(--primary);">${noticeName(notice)}</h4>
          <p style="color:#666; font-size:0.9rem;">${notice.publishDate || ''}</p>
          <hr>
          ${notice.content ? `<p>${notice.content}</p>` : ''}
          ${notice.pdfUrl ? `
            ${pdfLink(notice.pdfUrl, 'ডাউনলোড')}
            <div class="mt-2">
              <object data="${pdfUrl(notice.pdfUrl)}" type="application/pdf" class="pdf-frame">
                <a href="${pdfUrl(notice.pdfUrl)}" target="_blank" class="btn btn-primary btn-sm mt-2">
                  <i class="fas fa-external-link-alt me-1"></i>${_lang === 'bn' ? 'পিডিএফ খুলুন' : 'Open PDF'}
                </a>
              </object>
            </div>` : ''}
        </div>
      </div>`;
  }

  // ── GALLERY ────────────────────────────────────────────────────
  function renderGallery() {
    app().innerHTML = `
      <div style="max-width:900px; margin:0 auto;">
        <div class="content-panel text-center py-5">
          <i class="fas fa-video fa-3x mb-3" style="color:#ccc;"></i>
          <p class="text-muted">${_lang === 'bn' ? 'ভিডিও গ্যালারি শীঘ্রই আসছে' : 'Video gallery coming soon'}</p>
        </div>
      </div>`;
  }

  // ── UTILS ──────────────────────────────────────────────────────
  function escAttr(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
      .replace(/</g, '&lt;');
  }

  // ── PUBLIC API ─────────────────────────────────────────────────
  return {
    init:         init,
    toggleLang:   toggleLang,
    goNoticePage: goNoticePage,
  };

})();

// boot
App.init();
