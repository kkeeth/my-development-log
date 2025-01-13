# Recoil アーカイブ

GitHub リポジトリ
https://github.com/facebookexperimental/Recoil

## 台本

皆さんこんにちは。「雨宿りと WEB の小噺」へようこそ！ポッドキャスト配信者の Keeth こと桑原です。

この番組は，日々降り注ぐ情報の中でちょっと雨宿りしながら、様々な Web テクノロジーの成り立ちや裏話を小噺としてお届けする番組です．

今回の話題は「フロントエンドの状態管理ライブラリ Recoil リポジトリがアーカイブされた件」について．

### 本題

- すでに何名もブログに書いたり，𝕏 で元メンテナの方とやり取りをされていたりしている
- ネットを調べる限りはレイオフが原因
  - 元々 Meta 社は大量レイオフをしたことがあり，その時 Recoil の開発者およびメンテナもレイオフされていた
  - 今回ついに最後の一人もレイオフされることになり，アーカイブに至った模様
- > Although tons of internal projects still use it, no one wanted to take over the responsibility
  > 多くの社内プロジェクトでまた Recoil を使っていたのに，誰もその責任を引き継ごうとしなかった
  - と言っているのを見る限りいろいろ察する
  - https://x.com/mengdi_en/status/1875916781950468341
- 元々は OSS として世界中で使われることは想定していなかったらしい
  - とあるチームが作った状態管理のツール
  - 他のチームにも便利だと思ったので公開しただけ
  - react チームも，これが公式のライブラリだと主張したことはなく，むしろ推奨する唯一の状態管理ライブラリは react だと言っている
- 更新がずっと止まっている
  - リポジトリの最後の更新が 2023 年 9 月 8 日
  - 公式ブログも，2023 年の 3 月 1 日から更新がない
    - リンク: https://recoiljs.org/blog/2023/03/01/recoil-0.7.7-release
  - そもそもブログのページに見えているが，単なるリリースノート
- 色んな意見
  - Jotai への移行を促す良い機会と捉えるヒト
    - Jotai の開発者の一人は元々 Recoil の開発者でもあった
  - 良くも悪くも Recoil が公式状態管理ライブラリという捉え方をされていて，これがアーカイブされたことで React のエコシステムの多様化につながるとも考えられる
  - 大企業による OSS の持続可能性や，コミュニティとの連携の重要性を再認識，改めて考えさせられる事象だった
    - 一部では，Meta 社のオープンソースコミュニティに対する姿勢に疑問を投げる声もある
  - 一方で，Recoil は安定していたと言えばしていたので，このライブラリを利用していたプロジェクトは新たにライブラリの移行を検討せねばならず，その工数が取られる（幸いにも選択肢はいくつもあり，それほどドラスティックな違いはない）
  -
- 代替

  - npm trends を見る限りは， [Jotai]() か [Zustand]() の２択じゃないかなと
  - 元メンテナの人の 𝕏 のポストでは，`Jotai` の思想と設計が `Recoil` に非常に似ているとのこと
    - https://x.com/mengdi_en/status/1876089360078258646
  - `Zedux` という後継ライブラリも作られている
  - > Recoil paved the way for some amazing new tech. I'm glad it taught us the atomic model.
    > As many have said, Jotai is a great, lightweight alternative. We're also building Zedux as a full replacement for Recoil.
  - リポジトリ：https://github.com/Omnistac/zedux
  - 公式サイト：https://omnistac.github.io/zedux/
  - 気になったのでちょっとだけ見てみた
    - シンプルさ，ハイパフォーマンス（高速な状態の更新，最小限の再レンダリング），柔軟性，TypeScript との親和性 を謳っている
    - リリースノートを見た感じ [v0.5.7](https://github.com/Omnistac/zedux/releases/tag/v0.5.7) がスタートだが，[initial commit](https://github.com/Omnistac/zedux/commit/f76992961dc6c9272a30e8720e8df61c21a36bfa) は 2017 年 12 月 19 日と，実に 7 年とちょっと前からこのプロジェクトは開始している
    - `Molcular（分子の，分子からなる）` という概念がある
      - 昨今の状態ライブラリによくある `Atoms` や `Atomic（原子の）` の概念の上位概念
      - もちろん zedux にもある
    - > Atoms talk to each other. These connections form a graph. Ecosystems control and manipulate the graph.
    - atoms 同士がコミュニケーションするように設計されていて，その繋がりがいわゆるグラフを形成する．これが Molecular を表していて，エコシステム側でこのグラフをコントロールするらしい
  - その他，色々対応はきっちりしている
    - testable（`completely outside react`と言っているので，react 以外のフレームワークでも行けそう？）, SSR 互換，最小限のボイラープレート，Rx
  - 面白い話
    - > An honest recommendation first: If you're using a combination of React Query, Zustand, Recoil, Jotai, and/or XState, and you haven't encountered any shortcomings with your setup, you probably don't need Zedux.
      > もしあなたが React Query、Zustand、Recoil、Jotai、XState を組み合わせて使っていて、そのセットアップで何の欠点も感じていないのであれば、おそらく Zedux は必要ないだろう。
    - もしコードスプリッティングを使っているなら，zedux を使うのが楽しくなるかもしれない，というコメントが気になる
    - 興味深いのは，RxJS のサポートを強調していた
    - > edux was designed to handle everything. There should be absolutely no app requirements that Zedux can't handle well.
      > Zedux はすべてを処理できるように設計されている。Zedux がうまく扱えないアプリの要件は絶対にないはずだ。
      - 強い
    - 基本的には，Zustand, Jotai 等を使っているなら，それで十分という姿勢は崩さない
      - zedux も小規模なプロジェクトに最適
    - １つ大きなボーナス
      - スケールに強く設計されているので，アプリが時間とともに大きく複雑になったとしても、Zedux はその複雑さをエレガントに管理することができる，とな
  - 気になったので，個人でも触ってみようかなと思った

### エンディング

さて、そろそろ今回もお時間になりましたのでエンディングです．

この番組面白かったよーという方は，ぜひチャンネル登録もお願いします．もし聴いていて気になることや、話してほしいトピック，感想などありましたら、概要欄のフォームや，𝕏 でハッシュタグ「WEB 小噺」でつぶやいてください！web はアルファベット，「小噺」は漢字でもひらがなでも大丈夫です！

それでは、また雨宿りしに来てください。今回もお聴きくださりありがとうございました！「雨宿りと WEB の小噺」お相手は Keeth でした。さようなら！
