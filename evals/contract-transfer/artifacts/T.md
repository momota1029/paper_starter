# An iteration with a residual certificate

## The problem

Let \(n\) be a positive integer, let \(A=(A_{ij})_{i,j=1}^n\) be a real \(n\times n\) matrix, and let \(b\in\mathbb R^n\). Assume that \(A_{ij}\geq0\) and \(\sum_{j=1}^n A_{ij}=1\) for every row \(i\). We seek a vector \(x^*\in\mathbb R^n\) satisfying
\[
x^*=b+\tfrac12 Ax^*.
\]
Define \(F:\mathbb R^n\to\mathbb R^n\) by \(F(x)=b+\tfrac12 Ax\). A fixed point of \(F\) is a vector \(x^*\) with \(F(x^*)=x^*\), so it solves this equation.

Starting from any \(x_0\in\mathbb R^n\), form \(x_{k+1}=F(x_k)\) for integers \(k\geq0\). We measure vector size with the maximum norm,
\[
\|v\|_\infty=\max_{1\leq i\leq n}|v_i|,
\qquad v\in\mathbb R^n.
\]
The error \(\|x_k-x^*\|_\infty\) involves the unknown solution. In contrast, the residual
\[
r_k=\|F(x_k)-x_k\|_\infty
    =\|x_{k+1}-x_k\|_\infty
\]
can be computed from the current vector. The question is whether this computable quantity certifies the error.

## The external error bound

The contraction lemma (N, §2, Lemma 2) supplies the needed bound. Its assumptions are that \(F:\mathbb R^n\to\mathbb R^n\) satisfies
\[
\|F(x)-F(y)\|_\infty\leq q\|x-y\|_\infty
\quad\text{for all }x,y\in\mathbb R^n,
\]
for a constant \(q\) with \(0\leq q<1\). Thus the distance between two outputs is at most a fixed fraction of the distance between their inputs. Under these assumptions, \(F\) has a unique fixed point \(x^*\), every iteration from \(x_0\in\mathbb R^n\) converges to it, and, for every integer \(k\geq0\),
\[
\|x_k-x^*\|_\infty
\leq\frac{\|x_{k+1}-x_k\|_\infty}{1-q}.
\]
The denominator converts a single successive difference into a bound on the remaining distance to the solution.

## Applying the bound

For any \(x,y\in\mathbb R^n\) and any \(i\in\{1,\ldots,n\}\), the nonnegative entries and unit row sum give
\[
|(A(x-y))_i|
\leq\sum_{j=1}^n A_{ij}|x_j-y_j|
\leq\sum_{j=1}^n A_{ij}\|x-y\|_\infty
=\|x-y\|_\infty.
\]
Taking the maximum over rows and using \(F(x)-F(y)=\tfrac12 A(x-y)\), we obtain the lemma's inequality with \(q=\tfrac12\). This constant works for every allowed \(A\) and \(b\), independently of the initial vector. The domain, norm, and bound therefore match the lemma's assumptions. It follows that the equation has a unique solution, the iterates converge to it, and
\[
\|x_k-x^*\|_\infty\leq 2r_k
\quad(k\geq0).
\]
For any prescribed tolerance \(\varepsilon>0\), stopping when \(r_k\leq\varepsilon/2\) guarantees error at most \(\varepsilon\) for the vector \(x_k\). The residual computation uses \(x_{k+1}\), but this certificate bounds the error of \(x_k\).

## A two-coordinate example

Take \(n=2\), \(A=\begin{pmatrix}0&1\\1&0\end{pmatrix}\), and \(b=(1,0)\). Write the fixed point as \(x^*=(u,v)\), with \(u,v\in\mathbb R\). Its equations are \(u=1+v/2\) and \(v=u/2\); substituting the second into the first gives \(x^*=(4/3,2/3)\).

With \(x_0=(0,0)\), the first three iterates are \(x_1=(1,0)\), \(x_2=(1,1/2)\), and \(x_3=(5/4,1/2)\). Hence \(r_2=1/4\), which certifies \(\|x_2-x^*\|_\infty\leq1/2\). Direct comparison with the solution gives error \(1/3\), consistent with the certificate. The vector \((1,1/2)\) is an intermediate iterate rather than the fixed point.
