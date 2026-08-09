/**
 * 雨宿りとWEBの小噺.fm - Podcast Automation Webhook
 *
 * デプロイ手順:
 *   1. Google スプレッドシートを開く
 *   2. メニュー → 拡張機能 → Apps Script
 *   3. このコードを貼り付けて保存
 *   4. デプロイ → デプロイを管理 → 既存デプロイを編集 → バージョン「新バージョン」→ デプロイ
 *      ※ 新規デプロイにすると URL が変わり，デスクトップアプリの定期タスクが動かなくなる
 *   5. 実行ユーザー: 自分 / アクセス: 全員
 *
 * 受け付けるアクション:
 *   【既存・デスクトップアプリの定期タスクが使用。トークン不要】
 *   - update_episode  : エピソード行のステータス・配信日を更新
 *   - update_stock    : 企画ストック行の「使用/ボツ」を更新
 *
 *   【追加・Claude Code の podcast-publish-log skill が使用。トークン必須】
 *   - tabs        : タブ名と gid の一覧
 *   - header      : 指定タブのヘッダ行
 *   - rows        : 指定タブの全行
 *   - find        : ヘッダ名で列を指定して値を検索し、行番号を返す
 *   - append_row  : ヘッダ名をキーにした連想配列で 1 行追記
 *   - update_row  : ヘッダ名で行を特定し、指定フィールドだけを更新
 *
 * 追加分の書き込みはシート全体を書き換えられるため、API_TOKEN で保護している。
 *   プロジェクトの設定 → スクリプト プロパティ に `API_TOKEN` を追加すること
 *   （値は `openssl rand -hex 32` などで生成）。
 * 既存の 2 アクションは後方互換のためトークン不要のまま。デスクトップアプリ側も
 * トークンを送るようにしたら REQUIRE_TOKEN_FOR_ALL を true にして全体を保護する。
 */

const SPREADSHEET_ID = '1XuV55f2pDiTu8UihiD9_1cZlvFMbRGsPrZpQhcx72fI';

/** 後方互換のためトークン検証を免除するアクション */
const LEGACY_ACTIONS = ['update_episode', 'update_stock'];

/** デスクトップアプリ側がトークンを送るようになったら true にする */
const REQUIRE_TOKEN_FOR_ALL = false;

// ===== エントリポイント =====

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    const action = body.action;

    const needsToken = REQUIRE_TOKEN_FOR_ALL || LEGACY_ACTIONS.indexOf(action) === -1;
    if (needsToken) {
      const authError = checkToken_(body.token);
      if (authError) return json_(authError);
    }

    let result;
    switch (action) {
      // --- 既存（変更しないこと。デスクトップアプリの定期タスクが依存している）---
      case 'update_episode':
        result = updateEpisode(body.title, body.status, body.publishedDate, body.publishedYearMonth);
        break;
      case 'update_stock':
        result = updateStock(body.title, body.usage);
        break;

      // --- 追加 ---
      case 'tabs':
        result = ok_(listTabs_());
        break;
      case 'header':
        result = ok_(readHeader_(requireSheet_(body.tab)));
        break;
      case 'rows':
        result = ok_(readRows_(requireSheet_(body.tab), body.max));
        break;
      case 'find':
        result = ok_(findRows_(requireSheet_(body.tab), body.keyCol, body.key));
        break;
      case 'append_row':
        result = ok_(appendRow_(requireSheet_(body.tab), body.fields));
        break;
      case 'update_row':
        result = ok_(updateRow_(requireSheet_(body.tab), body.keyCol, body.key, body.fields));
        break;

      default:
        result = { success: false, error: 'Unknown action: ' + action };
    }

    return json_(result);
  } catch (err) {
    return json_({ success: false, error: err && err.message ? err.message : String(err) });
  }
}

// GET でのヘルスチェック用
function doGet(e) {
  return json_({ status: 'ok', timestamp: new Date().toISOString() });
}

// ===== エピソード管理シートの更新（既存・変更なし）=====
// 列: No / タイトル / カテゴリ / 配信予定日 / 配信日 / ステータス / ...

function updateEpisode(title, status, publishedDate, publishedYearMonth) {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = findSheetByHeader_(ss, 'タイトル', '配信日');
  if (!sheet) return { success: false, error: 'Episode sheet not found' };

  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  const titleCol   = headers.indexOf('タイトル');
  const statusCol  = headers.indexOf('ステータス');
  const dateCol    = headers.indexOf('配信日');

  for (let i = 1; i < data.length; i++) {
    if (String(data[i][titleCol]).trim() === String(title).trim()) {
      const row = i + 1;
      if (status)             sheet.getRange(row, statusCol + 1).setValue(status);
      if (publishedDate)      sheet.getRange(row, dateCol + 1).setValue(publishedDate);
      return { success: true, updatedRow: row, title: title };
    }
  }
  return { success: false, error: 'Title not found in episode sheet: ' + title };
}

// ===== 企画ストックシートの更新（既存・変更なし）=====
// 列: No. / カテゴリ / タイトル案 / メモ / 使用/ボツ / 使用エピソード番号

function updateStock(title, usage) {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = findSheetByHeader_(ss, 'タイトル案', '使用/ボツ');
  if (!sheet) return { success: false, error: 'Stock sheet not found' };

  const data = sheet.getDataRange().getValues();
  const headers = data[0];
  const titleCol = headers.indexOf('タイトル案');
  const usageCol = headers.indexOf('使用/ボツ');

  for (let i = 1; i < data.length; i++) {
    if (String(data[i][titleCol]).trim() === String(title).trim()) {
      const row = i + 1;
      sheet.getRange(row, usageCol + 1).setValue(usage);
      return { success: true, updatedRow: row, title: title };
    }
  }
  return { success: false, error: 'Title not found in stock sheet: ' + title };
}

// ===== 追加アクションの実装 =====
// 列の指定はすべて「ヘッダ名」で行う。列の位置は増減し得るので，
// 位置指定（A 列 / 3 番目）で書き込むと列が増えた瞬間に別の列を壊す。

function listTabs_() {
  return SpreadsheetApp.openById(SPREADSHEET_ID).getSheets().map(function (s) {
    return { title: s.getName(), gid: s.getSheetId(), lastRow: s.getLastRow() };
  });
}

function readHeader_(sheet) {
  const lastCol = sheet.getLastColumn();
  if (lastCol === 0) return [];
  return sheet.getRange(1, 1, 1, lastCol).getValues()[0].map(toText_);
}

function readRows_(sheet, max) {
  const lastRow = sheet.getLastRow();
  const lastCol = sheet.getLastColumn();
  if (lastRow === 0 || lastCol === 0) return [];
  const n = Math.min(lastRow, Number(max) || 200);
  return sheet.getRange(1, 1, n, lastCol).getValues().map(function (row) {
    return row.map(toText_);
  });
}

function findRows_(sheet, keyCol, key) {
  const headers = readHeader_(sheet);
  const col = headerIndex_(headers, keyCol);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  const values = sheet.getRange(2, col + 1, lastRow - 1, 1).getValues();
  const needle = String(key).trim();
  const hits = [];
  for (let i = 0; i < values.length; i++) {
    if (toText_(values[i][0]).trim() === needle) hits.push(i + 2);
  }
  return hits;
}

function appendRow_(sheet, fields) {
  const headers = readHeader_(sheet);
  const values = fieldsToRow_(headers, fields);
  return withLock_(function () {
    sheet.appendRow(values);
    return { row: sheet.getLastRow(), written: fields };
  });
}

function updateRow_(sheet, keyCol, key, fields) {
  if (!fields || typeof fields !== 'object') {
    throw new Error('fields は連想配列で指定してください');
  }
  const headers = readHeader_(sheet);
  const hits = findRows_(sheet, keyCol, key);
  if (hits.length === 0) throw new Error(keyCol + ' が「' + key + '」の行が見つかりません');
  if (hits.length > 1) {
    throw new Error(keyCol + ' が「' + key + '」の行が ' + hits.length + ' 件あります（行: ' +
                    hits.join(', ') + '）．どれを更新するか曖昧なので中断しました');
  }
  const row = hits[0];

  return withLock_(function () {
    const before = {};
    Object.keys(fields).forEach(function (name) {
      const col = headerIndex_(headers, name);
      const cell = sheet.getRange(row, col + 1);
      before[name] = toText_(cell.getValue());
      cell.setValue(fields[name]);
    });
    // 上書き前の値を返す．誤爆したときに戻せるようにするため
    return { row: row, before: before, after: fields };
  });
}

// ===== ユーティリティ =====

function checkToken_(token) {
  const expected = PropertiesService.getScriptProperties().getProperty('API_TOKEN');
  if (!expected) {
    return { success: false, error: 'API_TOKEN がスクリプトプロパティに未設定です' };
  }
  if (!token || !safeEquals_(String(token), expected)) {
    return { success: false, error: '認証に失敗しました' };
  }
  return null;
}

function requireSheet_(tab) {
  if (!tab) throw new Error('tab（タブ名）が指定されていません');
  const sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(tab);
  if (!sheet) throw new Error('タブが見つかりません: ' + tab + '（tabs で一覧を確認してください）');
  return sheet;
}

/** ヘッダ名 → 列インデックス（0 始まり）．見つからなければ落とす */
function headerIndex_(headers, name) {
  const i = headers.indexOf(String(name));
  if (i === -1) {
    throw new Error('ヘッダに「' + name + '」がありません．存在するのは: ' + headers.join(' / '));
  }
  return i;
}

/** {ヘッダ名: 値} を行配列に変換．未指定の列は空文字のまま残す */
function fieldsToRow_(headers, fields) {
  if (!fields || typeof fields !== 'object') {
    throw new Error('fields は連想配列で指定してください');
  }
  const row = new Array(headers.length).fill('');
  Object.keys(fields).forEach(function (name) {
    row[headerIndex_(headers, name)] = fields[name];
  });
  return row;
}

/** 排他制御．同時書き込みで行が壊れるのを防ぐ */
function withLock_(fn) {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(15000)) {
    throw new Error('他の処理が実行中です．しばらく待って再実行してください');
  }
  try {
    return fn();
  } finally {
    lock.releaseLock();
  }
}

/** 日付セルは yyyy-MM-dd に寄せる．JSON 経由で型が化けるのを防ぐ */
function toText_(v) {
  if (v instanceof Date) return Utilities.formatDate(v, Session.getScriptTimeZone(), 'yyyy-MM-dd');
  return v === null || v === undefined ? '' : String(v);
}

/** ダイジェスト比較．文字列の逐次比較よりタイミング差が出にくい */
function safeEquals_(a, b) {
  const ha = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, a);
  const hb = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, b);
  if (ha.length !== hb.length) return false;
  let diff = 0;
  for (let i = 0; i < ha.length; i++) diff |= ha[i] ^ hb[i];
  return diff === 0;
}

function ok_(result) {
  return { success: true, result: result };
}

function json_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

// ===== ユーティリティ: ヘッダーでシートを特定（既存）=====

function findSheetByHeader_(ss, col1, col2) {
  const sheets = ss.getSheets();
  for (const sheet of sheets) {
    const headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
    if (headers.includes(col1) && headers.includes(col2)) return sheet;
  }
  return null;
}
