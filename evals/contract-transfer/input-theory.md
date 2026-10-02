# 評価専用の架空の数学素材

依頼: 次の短稿を資料に即して整え、専門外の入力の説明を補い、作業上の確認を
別報告に残す。新規性の主張は不要。原稿は英語、900語以内。

## 読者とプロジェクト契約

読者は有限次元線形代数と三角不等式を知るが、固定点の反復誤差評価は知らない。
hard: 借りた補題の初出で出典と補題番号を付ける。使用するノルム、定義域、
定数、補題の仮定と結論、今回の代入を本文で読めるようにする。
strong: 問題→外部の道具→適用→数値例という順。weak: 節見出しの具体的な語。
hard の逸脱承認は与えられていない。通常の語順・見出し選択は執筆者に委ねる。
コーパスは今回供給された教材一件のみであり、二〜四本の実論文調査を実施したと
書かない。これは未調査条件を明記した試験用短稿である。

## 供給資料 N（本テストのための独自教材。実在文献ではない）

N §2, Lemma 2: On R^n with the maximum norm ||x||∞=max_i |x_i|, let F satisfy
||F(x)-F(y)||∞ ≤ q||x-y||∞ for every x,y, where 0≤q<1. For x_(k+1)=F(x_k),
there is a unique fixed point x*. For every k≥0,
||x_k-x*||∞ ≤ ||x_(k+1)-x_k||∞/(1-q).
Proof: successive differences are bounded by q^j||x_1-x_0||∞. Their sum is
finite, so iterates are Cauchy in R^n and converge. The Lipschitz bound gives
continuity and hence a fixed point. Two fixed points have distance at most q
times their distance, so coincide. Summing the tail starting at step k gives
the displayed residual bound.

Application: n is any positive integer, A is a real n×n matrix with nonnegative
entries and each row sums to one; b is any vector in R^n. F(x)=b+(1/2)Ax.
Since |(A(x-y))_i|≤sum_j A_ij ||x-y||∞=||x-y||∞, q=1/2 is admissible.
Example n=2, A swaps the coordinates, b=(1,0): solve x1=1+x2/2, x2=x1/2.

## 原稿

# An iteration with a residual certificate

Let A be a stochastic matrix and put F(x)=b+Ax/2. Iterating F converges to a
unique solution, and its residual bounds the error. This gives a stopping rule.

By the contraction lemma the assertion follows. The residual is at most half
the error, so stopping with residual ε guarantees error ε/2. In the two-coordinate
example with a swap matrix and b=(1,0), the fixed point is (1,1/2).
