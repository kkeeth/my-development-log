# Stripeの決済は見えないところで何度も試みている　〜リトライロジックの美学〜

> **配信ステータス**：未配信
> **配信URL**：（配信済みになったら記入）

## 導入

はい、どうもこんにちは。「雨宿りとWEBの小噺」、始まりました。Keethこと桑原です。
この番組では、Webテクノロジーの歴史や裏側にある、ちょっとした小噺を紹介しています。

**つかみ**

- サブスク更新日に残高足りなかったのに、気づいたら継続してた経験ない？
- あれ、Stripeがこっそりリトライしてる

**基本の仕組み**

- デフォルトで最大3回リトライ＝合計4回試行
- 「3回リトライ」は3回に聞こえるが初回失敗を含めると4回、これ意外と知られてない
- 失敗するとwebhookで通知が飛ぶ（開発者向けの話）
- 📎 https://blog.stunning.co/quick-tip-stripe-attempts-to-pay-invoices-up-to-4-times-not-3/

**Smart Retries（ここが面白い）**

- ただ一定間隔で再試行してるわけじゃない
- 数十億件のトランザクションで学習したMLモデルがタイミングを判断
- 深夜2時の失敗→翌朝10時に再試行する方が成功率高い（残高が回復してる）
- 考慮してる要素：時間帯・曜日・月のどの週・顧客とビジネスの地域・カードの過去の成功率
- デフォルトは2週間以内に最大8回
- 📎 https://stripe.com/blog/how-we-built-it-smart-retries
- 📎 https://docs.stripe.com/billing/revenue-recovery/smart-retries

**開発者目線のリトライ設計の話（小噺）**

- リトライの基本思想はExponential Backoff（指数バックオフ）
- 100ms→200ms→400ms→と間隔を伸ばす
- さらにJitter（ランダムな揺らぎ）を加えてリクエストの集中を防ぐ
- Stripeはこれを決済というシビアな文脈でMLと組み合わせてる
- 📎 https://www.tomaszezula.com/implementing-smart-retries-with-stripe/

**美学の話（締め）**

- このリトライ、ユーザーには完全に見えない
- 失敗してる、でも諦めない、静かに試み続ける
- 「失敗しないように作る」じゃなくて「失敗しても回復できるように作る」という設計思想
- Stripeの調査：リトライで回収した顧客はその後平均7ヶ月継続＝新規顧客獲得と同じ価値
- 📎 https://stripe.com/resources/more/payment-retries-101
