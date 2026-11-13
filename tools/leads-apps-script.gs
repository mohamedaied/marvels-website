/**
 * Marvels — تسجيل طلبات فورمات الموقع في Google Sheet
 * ----------------------------------------------------
 * 1. غيّر KEY تحت لكلمة سر طويلة من عندك (دي اللي هتكتبها في صفحة الطلبات في لوحة التحكم).
 * 2. لو عايز إيميل بكل طلب جديد، اكتب إيميلك في NOTIFY_EMAIL (أو سيبه فاضي).
 * 3. Deploy ← New deployment ← Web app:
 *      Execute as: Me      Who has access: Anyone
 * 4. انسخ لينك الـWeb app وحطه في لوحة التحكم ← التواصل والإعدادات ← "لينك تسجيل الطلبات".
 */
const KEY = 'CHANGE-ME-to-a-long-secret';
const NOTIFY_EMAIL = '';
const SHEET_NAME = 'الطلبات';

// [اسم الحقل اللي جاي من الموقع, عنوان العمود في الشيت]
const COLS = [
  ['_ts', 'التاريخ والوقت'],
  ['form', 'الفورم'],
  ['f_name', 'الاسم'],
  ['f_phone', 'الموبايل'],
  ['f_business', 'البيزنس'],
  ['f_field', 'المجال'],
  ['f_link', 'الصفحة'],
  ['f_goal', 'الهدف'],
  ['f_budget', 'ميزانية الإعلانات'],
  ['f_type', 'نوع الحجز'],
  ['f_date', 'يوم الحجز'],
  ['f_time', 'ساعة الحجز'],
  ['f_hours', 'المدة'],
  ['f_people', 'عدد الأشخاص'],
  ['f_notes', 'ملاحظات العميل'],
  ['lang', 'اللغة'],
  ['page', 'صفحة الموقع'],
  ['_status', 'الحالة'],
  ['_team', 'ملاحظات الفريق'],
];

function sheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) {
    sh = ss.insertSheet(SHEET_NAME, 0);
    sh.appendRow(COLS.map(c => c[1]));
    sh.setFrozenRows(1);
    sh.getRange(1, 1, 1, COLS.length).setFontWeight('bold').setBackground('#12324A').setFontColor('#ffffff');
    sh.setRightToLeft(true);
    const statusCol = COLS.findIndex(c => c[0] === '_status') + 1;
    sh.getRange(2, statusCol, 1000, 1).setDataValidation(
      SpreadsheetApp.newDataValidation().requireValueInList(['جديد', 'اتكلمنا معاه', 'حجز جلسة', 'بقى عميل', 'مش مهتم'], true).build());
  }
  return sh;
}

function clean_(v) {
  v = String(v == null ? '' : v).slice(0, 1000);
  return v ? "'" + v : '';   // يمنع تنفيذ الصيغ ويحافظ على الصفر في أول رقم الموبايل
}

function doPost(e) {
  const p = (e && e.parameter) || {};
  if (p.website_hp || !p.form) return json_({ ok: false });
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const row = COLS.map(([k]) => {
      if (k === '_ts') return new Date();
      if (k === '_status') return 'جديد';
      if (k === '_team') return '';
      return clean_(p[k]);
    });
    sheet_().appendRow(row);
  } finally {
    lock.releaseLock();
  }
  if (NOTIFY_EMAIL) {
    const body = COLS.filter(([k]) => p[k]).map(([k, t]) => t + ': ' + p[k]).join('\n');
    MailApp.sendEmail(NOTIFY_EMAIL, 'طلب جديد من الموقع — ' + (p.f_name || ''), body);
  }
  return json_({ ok: true });
}

function doGet(e) {
  const p = (e && e.parameter) || {};
  if (!KEY || KEY.indexOf('CHANGE-ME') === 0 || p.key !== KEY) return json_({ ok: false, error: 'unauthorized' });
  const sh = sheet_();
  const range = sh.getDataRange();
  const shown = range.getDisplayValues(), raw = range.getValues();
  const keep = [];
  for (let i = 1; i < shown.length; i++) if (shown[i].join('') !== '') keep.push(i);
  return json_({
    ok: true,
    headers: shown[0] || [],
    rows: keep.map(i => shown[i]),
    ts: keep.map(i => raw[i][0] instanceof Date ? raw[i][0].getTime() : null),
    sheetUrl: SpreadsheetApp.getActiveSpreadsheet().getUrl(),
  });
}

function json_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
