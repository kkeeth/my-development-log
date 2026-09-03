#!/usr/bin/env node
// 台本の配信ステータスを一覧する．引数でシーズンを絞れる（既定は全シーズン）
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { join } from "node:path";

const BASE = "src/PODCASTS/WEB小噺";
const ORDER = { 配信済み: 0, 要確認: 1, 未配信: 2 };
const MARK = { 配信済み: "●", 要確認: "?", 未配信: "○" };

const seasons = process.argv[2]
  ? [process.argv[2]]
  : readdirSync(BASE, { withFileTypes: true })
      .filter((d) => d.isDirectory() && d.name.startsWith("Season"))
      .map((d) => d.name)
      .sort();

for (const season of seasons) {
  const dir = join(BASE, season);
  if (!existsSync(dir)) {
    console.error(`${season} が見つかりません`);
    process.exitCode = 1;
    continue;
  }

  const rows = readdirSync(dir)
    .filter((f) => f.endsWith(".md"))
    .map((f) => {
      const body = readFileSync(join(dir, f), "utf8");
      const status = body.match(/配信ステータス\*\*：(.+)/)?.[1].trim() ?? "ヘッダー無し";
      // エピソード番号は配信メタの採用タイトル行だけから拾う（本文の番号付きリストを誤検出しないため）
      const ep = body.match(/### タイトル\s*\n+\s*(\d+)\. /)?.[1] ?? "";
      const title = body.match(/^# (.+)$/m)?.[1] ?? f;
      return { status, ep, title, slug: f.replace(/\.md$/, "") };
    })
    .sort(
      (a, b) =>
        (ORDER[a.status] ?? 9) - (ORDER[b.status] ?? 9) ||
        (Number(a.ep) || 999) - (Number(b.ep) || 999) ||
        a.slug.localeCompare(b.slug),
    );

  const tally = rows.reduce((acc, r) => ({ ...acc, [r.status]: (acc[r.status] ?? 0) + 1 }), {});
  const summary = Object.entries(tally)
    .map(([k, v]) => `${k} ${v}`)
    .join(" / ");
  console.log(`\n${season}  (${rows.length}本: ${summary})`);

  for (const r of rows) {
    const mark = MARK[r.status] ?? "!";
    const ep = (r.ep ? r.ep : "-").padStart(3);
    console.log(`  ${mark} ${r.status.padEnd(4)} ${ep}  ${r.slug}`);
    console.log(`             ${r.title}`);
  }
}
