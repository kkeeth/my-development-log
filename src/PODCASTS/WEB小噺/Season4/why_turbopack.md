# Turbopack の思想

元記事

https://turbo.build/pack/docs/why-turbopack

以下，原文と訳

> When we set out to create Turbopack, we wanted to solve a problem. We had been working on speed improvements for Next.js. We migrated away from several JS-based tools. Babel, gone. Terser, gone. Our next target was another JS-based tool, webpack.
>
> Replacing it became our goal. But with what?
>
> A new generation of native-speed bundlers were emerging, but after assessing the bundlers on the market, we decided to build our own. Why?
>
> Turbopack の開発に着手したとき、私たちはある問題を解決したいと考えました。 私たちは、Next.js のスピード改善に取り組んでいました。 いくつかの JS ベースのツールから移行しました。 Babel はなくなった。 Terser もなくなった。 私たちの次のターゲットは、別の JS ベースのツールである webpack だった。
> webpack を置き換えることが私たちの目標になった。 しかし，何を持って？
> 新世代のネイティブスピードバンドラーが登場しつつありましたが、市場に出回っているバンドラーを評価した結果、私たちは自分たちで作ることにしました。 なぜか？

> ## Unified Graph
> A large reason why frameworks like Next.js have become so popular is that implementing features like SSR (and now RSC) with the current generation of bundlers is non-trivial. You need to create multiple compilers for each output environment (browser, server, etc), and manage the communication between them so that their bundles end up correctly stitched together.
>
> We wanted to remove this maintenance burden from Next.js and any framework that chooses to use Turbopack. We can also create a cleaner and more stable implementation by designing a single unified graph that can be used to generate bundles for multiple environments. 
>
> ## 統一されたグラフ
>  Next.jsのようなフレームワークがこれほど普及した大きな理由は、SSR（そして現在はRSC）のような機能を現在の世代のバンドルで実装することが、自明ではないからです。 出力環境（ブラウザ、サーバーなど）ごとに複数のコンパイラを作成し、それらのバンドルが正しく結合されるように、コンパイラ間の通信を管理する必要があります。 
> 私たちは、Next.jsや、Turbopackを使用するフレームワークから、このようなメンテナンスの負担を取り除きたかったのです。 また、複数の環境用のバンドルを生成するために使用できる単一の統一されたグラフを設計することで、よりクリーンで安定した実装を作成できます。

> ## Bundling vs Native ESM
> Frameworks like Vite use a technique where they don’t bundle application source code in development mode. Instead, they rely on the browser’s native ES Modules system. This approach results in incredibly responsive updates since they only have to transform a single file.
>
> We experimented with this approach, but ran into scaling issues with large applications made up of many modules. A flood of cascading network requests in the browser lead to a relatively slow startup time. For the browser, it’s faster if it can receive the code it needs in as few network requests as possible - even on a local server.
>
> That’s why we decided that, like webpack, we wanted Turbopack to bundle the code in the development server. Turbopack can do it much faster, especially for larger applications, because it is written in Rust and skips optimization work that is only necessary for production.
>
> バンドル vs ネイティブESM Viteのようなフレームワークは、開発モードでアプリケーションのソースコードをバンドルしないテクニックを使っている。 その代わりに、ブラウザのネイティブESモジュールシステムに依存します。 
> このアプローチでは、単一のファイルを変換するだけなので、驚くほど応答性の高いアップデートが実現します。 このアプローチで実験を行いましたが、多くのモジュールで構成される大規模なアプリケーションでは、スケーリングの問題が発生しました。 ブラウザにカスケードするネットワーク・リクエストの洪水が発生すると、起動時間が比較的遅くなるのだ。 そのため、webpackのようにTurbopackで開発サーバーのコードをバンドルすることにしました。 Turbopackは、Rustで書かれており、本番環境でのみ必要な最適化作業を省略できるため、特に大規模なアプリケーションでは、より高速に実行できます。

## 台本

皆さんこんにちは。「雨宿りと WEB の小噺」へようこそ！ポッドキャスト配信者の Keeth こと桑原です。

この番組は，日々降り注ぐ情報の中でちょっと雨宿りしながら、様々な Web テクノロジーの成り立ちや裏話を小噺としてお届けする番組です．

今回の話題は「Next.js で使うことができるバンドラ Turbopack」について．

### 本題

-
