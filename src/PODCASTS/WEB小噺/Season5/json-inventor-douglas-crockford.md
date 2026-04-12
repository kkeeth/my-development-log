# JSONを「発明」した男は「俺は発見しただけだ」と言った

## 台本

### オープニング

【ジングル】
はい、どうもこんにちは。「雨宿りと WEB の小噺」、始まりました。Keeth こと桑原です。
今回もちょっとだけ、雨宿りしていきませんか。
今回のお題はですね、「JSONを『発明』した男は『俺は発見しただけだ』と言った」。ちょっと面白い話なんで、まぁ聞いてってください。

### 本題

- **JSONを作ったのはDouglas Crockford（ダグラス・クロックフォード）という人物**
  - 1975年、サンフランシスコ州立大学で「ラジオ・テレビ学」を専攻して卒業。つまりコンピュータサイエンス科じゃない
  - 大学の授業でFORTRANに触れ、学内の計算機室に通いつめてプログラミングにハマっていく

- **最初のキャリアはAtariでゲームを作っていた**
  - 1980年、Atari 8ビット機を購入。「Galahad and the Holy Grail」というゲームをAtari Program Exchange（APX）向けに投稿
  - そのゲームが当時Atari社員だったChris Crawfordの目に留まり、Atariにスカウトされるという棚ぼた採用
  - Atariでは「Burgers!」などのゲームや実験的なオーディオ・ビジュアルのデモを制作
  - そう、JSONを生み出した人は元ゲームクリエイター

- **Lucasfilm（ルーカスフィルム）で世界初のオンラインRPGに関わる**
  - 1984年、あのスター・ウォーズのルーカスフィルムにテクノロジーディレクターとして入社
  - ILM（インダストリアル・ライト＆マジック）やTHXのプロジェクトにも関与しながら、「Habitat」というプロジェクトに携わる
  - Habitatは今でいうMMORPGの先祖にあたる、世界初規模のグラフィカルなオンライン仮想空間
  - 後のSecond Lifeにも通じるこの経験が、後の「つながりの設計」への問題意識を育てた

- **Electric Communitiesを共同創業し、1990年代のバーチャルワールドに挑む**
  - Habitatで一緒だったChip Morningstar、Randy Farmerとともに1994年に創業
  - 「世界規模でスケールする分散型ネットワークプラットフォーム」を目指し、なんとVC調達額は4000万ドル
  - Second Lifeの先駆けとなる技術も開発していたが、時代が早すぎた
  - このChip Morningstarこそ、のちにJSONを一緒に「発見」する相棒

- **2001年、ガレージで人類初のJSONメッセージが送られた**
  - Crockfordが当時のシングルページアプリ（SPA）を作る会社「State Software」を立ち上げ、CTOに就任
  - 社名は最初「Veil（ヴェール）」という仮称だった。「後でアンベールする（=正式公開する）から」という理由
  - 2001年4月、CrockfordとChip Morningstarがガレージで歴史上初のJSONメッセージを送信
  - そのメッセージはHTMLドキュメントに埋め込まれた、セッションオブジェクト宛てのシンプルなテストデータだった

- **「俺はJSONを発明していない。発見しただけだ」という有名な言葉**
  - CrockfordはJSONについてこう語っている：「I do not claim to have invented JSON. I claim only that I discovered it. It existed in nature.（JSONを発明したとは言っていない。発見しただけだ。JSONはもともと自然界に存在していた）」
  - 実際、JavaScriptのオブジェクトリテラルをデータ転送に使う手法は、1996年にNetscapeのSlava Galperinが既に使っていたと記録されている
  - つまりCrockfordがやったのは「すでにJavaScriptの中に隠れていたものに名前をつけ、整理して世界に紹介した」こと
  - これDockerの「発明じゃなく整理した」発言と同じ匂いがしますよね

- **JSONの設計哲学：とにかく「小さくする」ことへの執念**
  - 設計原則は3つ：「最小限」「テキストベース」「JavaScriptのサブセット」
  - 「機能追加は全部拒否」というFeature Creep（機能の肥大化）への強い嫌悪感が根底にある
  - 「XMLはすごいものを作ろうとしすぎた。JSONはそうじゃない」というシンプルへの信念

- **json.orgを2002年に取得し、2006年にRFC 4627として正式標準化**
  - 委員会も組織も通さず、個人でドメインを取って仕様を公開するという異例のやり方で普及
  - RFC 4627はIETFのRFCのなかでも特に短くシンプルなことで有名。読める長さで書いてある
  - 余談だが、後にJSON5やJSONLなど派生形式も生まれ、「JSONの子孫」が今も増え続けている

- **Yahoo!、PayPalで「JavaScriptのご意見番」として活躍**
  - YahooのJavaScriptアーキテクトとして勤務し、コード品質ツール「JSLint」を開発
  - 2012年にPayPalへ移籍、シニアJavaScriptアーキテクトとして2019年まで在籍
  - 2008年に出版した「JavaScript: The Good Parts」は薄い本なのに業界のバイブル的存在に
  - この本で「JavaScriptには良い部分がある」と言ったことを本人は「異端だった」と表現している

- **現在のCrockfordは「JavaScriptを引退させるべきだ」と言っている**
  - 2022年、「今のJavaScriptにできる最善は引退させることだ」という過激な発言で話題に
  - 自分がJSONを通じて普及を助けたJavaScriptを、今度は「卒業させよう」と主張する皮肉な立場
  - ゲームを作りながらAtariに拾われ、ルーカスフィルムで仮想空間を作り、ガレージでJSONを発見し、世界標準を個人で作った男の、これが現在地

📎 https://en.wikipedia.org/wiki/Douglas_Crockford
📎 https://www.crockford.com/about.html
📎 https://nofluffjuststuff.com/blog/douglas_crockford/2008/01/the_discovery_of_json
📎 https://twobithistory.org/2017/09/21/the-rise-and-rise-of-json.html
📎 https://hackernoon.com/the-history-of-json-and-the-people-that-created-it
📎 https://devclass.com/2022/08/04/retire_javascript_says-json-creator-douglas-crockford/

### エンディング

【ジングル】
さて、そろそろ今回もお時間です。
面白かったよーという方は、ぜひチャンネル登録もお願いします。話してほしいトピックや感想は、概要欄のフォームか 𝕏 で「WEB 小噺」でつぶやいてください。web はアルファベット、「小噺」は漢字でもひらがなでも大丈夫です！
それでは、また雨宿りしに来てください。お相手は Keeth でした。さようなら！
【ジングル】
