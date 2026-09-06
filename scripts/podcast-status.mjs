#!/usr/bin/env node
// 台本の配信ステータスを一覧する．引数でシーズンを絞れる（既定は全シーズン）
// ステータスはフォルダーで決まる：直下 = 未配信，published/ = 配信済み，archived/ = ボツ
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { join } from "node:path";

const BASE = "src/PODCASTS/WEB小噺";
const BUCKETS = [
  { dir: "published", label: "配信済み", mark: "●" },
  { dir: "", label: "未配信", mark: "○" },
  { dir: "archived", label: "ボツ", mark: "×" },
];

const seasons = process.argv[2]
  ? [process.argv[2]]
  : readdirSync(BASE, { withFileTypes: true })
      .filter((d) => d.isDirectory() && d.name.startsWith("Season"))
      .map((d) => d.name)
      .sort();

for (const season of seasons) {
  const seasonDir = join(BASE, season);
  if (!existsSync(seasonDir)) {
    console.error(`${season} が見つかりません`);
    process.exitCode = 1;
    continue;
  }

  const rows = BUCKETS.flatMap(({ dir, label, mark }) => {
    const target = dir ? join(seasonDir, dir) : seasonDir;
    if (!existsSync(target)) return [];

    return readdirSync(target)
      .filter((f) => f.endsWith(".md"))
      .map((f) => {
        const body = readFileSync(join(target, f), "utf8");
        // エピソード番号は配信メタの採用タイトル行だけから拾う（本文の番号付きリストを誤検出しないため）
        const ep = body.match(/### タイトル\s*\n+\s*(\d+)\. /)?.[1] ?? "";
        const title = body.match(/^# (.+)$/m)?.[1] ?? f;
        return { label, mark, ep, title, slug: f.replace(/\.md$/, "") };
      })
      .sort(
        (a, b) =>
          (Number(a.ep) || 999) - (Number(b.ep) || 999) || a.slug.localeCompare(b.slug),
      );
  });

  const tally = rows.reduce((acc, r) => ({ ...acc, [r.label]: (acc[r.label] ?? 0) + 1 }), {});
  const summary = BUCKETS.filter(({ label }) => tally[label])
    .map(({ label }) => `${label} ${tally[label]}`)
    .join(" / ");
  console.log(`\n${season}  (${rows.length}本: ${summary})`);

  for (const r of rows) {
    const ep = (r.ep ? r.ep : "-").padStart(3);
    console.log(`  ${r.mark} ${r.label.padEnd(4)} ${ep}  ${r.slug}`);
    console.log(`             ${r.title}`);
  }
}
