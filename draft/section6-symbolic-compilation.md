# 6. From Axis Mappings to Attribute Programs

> **Draft status.** This section proposes a compilation algorithm and a conditional correctness result. The full proof and its connection to the implementation remain to be established. Author notes at the end list the remaining work.

Section 5 determines which axes to keep, checks their order, and constructs RHS attributes for given metadata. This section turns those steps into programs that work before tensor ranks and axis positions are known. Symbolic axis mapping tracks where axes occur. Partitioning splits groups when their axes have different roles. Attribute synthesis uses these groups and mappings to generate expressions over source metadata.

## 6.1. Compilation objective

For a fixed rewrite, the compiler produces two programs: $\widehat{\operatorname{check}}$ tests whether valid RHS attributes exist, and $\widehat{\operatorname{build}}$ constructs them when the check succeeds. Write $\llbracket e\rrbracket_p$ for evaluating program $e$ on metadata $p$. The goal is

$$
\llbracket\widehat{\operatorname{check}}\rrbracket_p
=\operatorname{check}(p),
$$

and, when this check succeeds,

$$
\llbracket\widehat{\operatorname{build}}\rrbracket_p
=\operatorname{build}(p).
$$

These equalities apply within Section 5's assumptions and the compilation boundary stated in Section 6.5. Both constructors use the same choices wherever the mathematical algorithm leaves an axis order unspecified.

The programs read shapes and source attributes, not tensor values. Their code is fixed, but the lists they process may have different lengths at each match.

We use dot reassociation throughout:

$$
T=\operatorname{dot}(X,Y),\qquad
O=\operatorname{dot}(T,Z)
\quad\Rightarrow\quad
U=\operatorname{dot}(Y,Z),\qquad
O'=\operatorname{dot}(X,U).
$$

To keep the example short, both source dots have no batch axes. The general construction also handles batch axes under Section 5's rules. Arithmetic is exact, as required by that section.

## 6.2. Symbolic axis mapping

A **symbolic group** is an ordered sequence of logical axes whose length is not yet known. An **interface** lists all axes of a tensor in dimension order. A mapping records where a group occurs:

$$
\operatorname{gather}(\mathsf I_t,q_G)=G.
$$

Here $q_G$ is a list expression giving the positions of group $G$ in tensor $t$. Two operand mappings for the same group pair axes in the same order. Equal sizes alone never establish that two axes are the same.

In the first source dot, let $K$ be the contracted group and $I,J$ the free groups of $X,Y$. Its mappings include

| Tensor | Group | Position list |
|---|---|---|
| $X$ | $I$ | $i_X$ |
| $X$ | $K$ | $k_X$ |
| $Y$ | $K$ | $k_Y$ |
| $Y$ | $J$ | $j_Y$ |
| $T$ | $I$ | $q_I=\operatorname{range}(|I|)$ |
| $T$ | $J$ | $q_J=|I|+\operatorname{range}(|J|)$ |

The lists $k_X,k_Y$ are captured contraction attributes. The free lists $i_X,j_Y$ are their ordered complements in the operand axes. The dot's output interface is $\mathsf I_T=I\Vert J$, where $\Vert$ concatenates sequences. Adding a number to a list adds it to every entry.

The compiler visits producers before consumers. At each operation, it records local mappings, aligns them through shared tensors, and records the output interface. It keeps the connections of summed axes even after those axes leave an output interface.

Mappings compose through position lists:

$$
\operatorname{gather}(\operatorname{gather}(\mathsf I,q),h)
=\operatorname{gather}(\mathsf I,\operatorname{gather}(q,h)).
$$

Thus, selecting positions $h$ within a known group gives positions $\operatorname{gather}(q,h)$ in the original tensor. This rule works for arbitrary group lengths.

## 6.3. Symbolic axis partitioning

A consumer can select axes from several producer groups. The compiler must split those selections by origin while keeping their partners.

Let $d_\ell,d_r$ be the second source dot's contraction lists in $T,Z$. They select a shared group $D$. Since $\mathsf I_T=I\Vert J$, the selected axes may come from both $I$ and $J$.

Define $\operatorname{matchPositions}(a,b)=(u,v)$ for lists with distinct entries. It finds their common entries in $a$'s order, returning positions such that

$$
\operatorname{gather}(a,u)=\operatorname{gather}(b,v).
$$

For each producer group $G\in\{I,J\}$, compute

$$
\begin{aligned}
(u_G,v_G)&=\operatorname{matchPositions}(d_\ell,q_G),\\
G_{\mathrm{sel}}&=\operatorname{gather}(G,v_G),\\
G_{\mathrm{rem}}&=\operatorname{gather}
\bigl(G,\operatorname{ordered\_complement}(\operatorname{range}(|G|),v_G)\bigr),\\
z_G&=\operatorname{gather}(d_r,u_G).
\end{aligned}
$$

The two position lists serve different purposes: $v_G$ selects axes within $G$, while $u_G$ locates their entries in the contraction list. Only $u_G$ selects the matching partners in $Z$.

For example, let $T$ have interface $[i_0,i_1,j_0,j_1]$. Suppose $d_\ell=[3,0]$ selects $[j_1,i_0]$, paired with $d_r=[2,0]$ in $Z$.

| Group | $u_G$: positions in $d_\ell$ | $v_G$: positions in $G$ | $z_G$: partner positions in $Z$ |
|---|---|---|---|
| $I$ | $[1]$ | $[0]$ | $[0]$ |
| $J$ | $[0]$ | $[1]$ | $[2]$ |

Using $v_I$ to select from $d_r$ would incorrectly pair $i_0$ with position 2 instead of position 0.

The selected and remaining groups are disjoint and cover the original group. Selected axes follow contraction order; remaining axes follow the original group order. Their concatenation need not recover the original order. The compiler therefore keeps their position mappings and the full ordered interface.

For other composed operations, the same split is applied when a group contains axes with different roles. The resulting groups must distinguish which inputs use each axis and whether it reaches the final output. Repeated refinement must preserve earlier mappings and their ordering.

## 6.4. Attribute program synthesis

The refined mappings supply the logical axes needed by Section 5. Synthesis follows its three passes.

**Choose retained axes.** Process the RHS from inputs to root. At each node, keep axes needed by the final output or an input outside the subtree, together with any axes the operation cannot remove. For a dot, shared required axes become batch axes; other shared axes are contracted. Axes present in only one operand remain free.

In the example, $U$ must keep $K$ to connect with $X$. It must also keep $I_{\mathrm{sel}}$, which reaches $U$ through $Z$ and later connects with $X$. It can contract $J_{\mathrm{sel}}$ because all its uses are inside $U$. Let $H$ denote the free axes of $Z$ in the source outer dot.

| RHS operation | Contracted axes | Retained axes |
|---|---|---|
| $U=\operatorname{dot}(Y,Z)$ | $J_{\mathrm{sel}}$ | $K,J_{\mathrm{rem}},I_{\mathrm{sel}},H$ |
| $O'=\operatorname{dot}(X,U)$ | $I_{\mathrm{sel}},K$ | $I_{\mathrm{rem}},J_{\mathrm{rem}},H$ |

This table shows membership, not intermediate output order.

**Check ordering.** Starting from the target output order, pass the required subsequences toward the inputs using Section 5's rules. Generate the local ordering checks and the root retained-set check. Their conjunction is $\widehat{\operatorname{check}}$. Each requirement must contain distinct axes from the node's retained set.

**Construct position lists.** Process the RHS from inputs to root again. Use each chosen group in the same order on both sides of a paired binding. For the inner replacement dot,

$$
k_\ell^U=\operatorname{gather}(j_Y,v_J),\qquad
k_r^U=z_J=\operatorname{gather}(d_r,u_J).
$$

Both lists select $J_{\mathrm{sel}}$. Let $f_Y,f_Z$ be their ordered complements in the axes of $Y,Z$. The constructed interface is

$$
\mathsf I_U=
\operatorname{gather}(\mathsf I_Y,f_Y)
\Vert\operatorname{gather}(\mathsf I_Z,f_Z).
$$

This preserves the operand orders, including interleaved groups. The compiler extends its mappings to this new interface.

The final dot contracts the ordered sequence $I_{\mathrm{sel}}\Vert K$. Its left list is

$$
k_\ell^{O'}=\operatorname{gather}(i_X,v_I)\Vert k_X.
$$

Its right list initially queries those groups in $\mathsf I_U$. Substituting the constructed interface gives an executable expression:

$$
k_r^{O'}=
\bigl(|f_Y|+\operatorname{pos}(f_Z,z_I)\bigr)
\Vert\operatorname{pos}(f_Y,k_Y).
$$

Here $\operatorname{pos}(a,b)$ returns the positions of entries of $b$ in list $a$, in $b$'s order. These queries compare source position lists; they no longer refer to logical groups. The shift $|f_Y|$ accounts for the left-free axes appearing first in $U$.

Removing the contracted axes leaves output order

$$
I_{\mathrm{rem}}\Vert J_{\mathrm{rem}}\Vert H,
$$

which matches the source. The RHS sums over $J_{\mathrm{sel}}$ inside $U$ and over $I_{\mathrm{sel}},K$ at the final dot. Together these are the source reduction axes $D,K$, with the same input pairings.

The general compiler follows this structure:

```text
Compile(rule):
    build source interfaces and axis mappings
    split groups where composed operations give their axes different roles
    compute RHS retained groups from inputs to root
    propagate ordering requirements from root to inputs
    construct RHS interfaces and attributes from inputs to root
    replace group queries in checks and attributes with metadata expressions
    return check_program, attribute_program
```

Both programs must contain only executable operations over source metadata. A query that cannot be resolved leaves compilation unfinished. No step enumerates concrete ranks or candidate attribute assignments.

## 6.5. Correctness and compilation scope

The proof connects the mapping and partitioning rules to Section 5 through three properties.

**Mapping preservation.** Each recorded mapping selects exactly the stated axes in the stated order. Local operation contracts establish the initial mappings; the gather-composition identity preserves them across operations.

**Partition preservation.** A split gives disjoint selected and remaining axes covering the original group. The lists $u_G,v_G$ preserve their correspondence, and $z_G$ preserves their operand partners. Keeping the ordered interface preserves the original layout even when groups interleave.

**Construction preservation.** Evaluating the symbolic retained sets, ordering checks, and attribute expressions gives the results of Section 5. The final conversion to metadata code preserves both results and definedness.

**Proposed theorem (conditional compilation preservation).** Suppose the source representation gives the exact LHS axis connections and output order, mapping and partitioning satisfy the properties above, and all generated operations have terminating, meaning-preserving translations to metadata code. Then, for every metadata instance in the admitted domain,

$$
\llbracket\widehat{\operatorname{check}}\rrbracket_p
=\operatorname{check}(p).
$$

When this check succeeds, the generated builder is defined and agrees with Section 5's builder, using the same ordering choices. Therefore,

$$
\llbracket\widehat{\operatorname{check}}\rrbracket_p
\iff\exists\beta:\operatorname{Valid}(p,\beta),
$$

and a successful check gives

$$
\operatorname{Valid}
\left(p,\llbracket\widehat{\operatorname{build}}\rrbracket_p\right).
$$

*Proof sketch.* First use mapping and partition preservation to establish the source axes and their positions. Induction over the three RHS passes then gives the same retained sets, ordering checks, and attributes as the mathematical algorithm. Successful checks ensure that each position query is defined. Meaning-preserving translation keeps these results in the emitted code. Section 5 supplies correctness and completeness of the resulting assignments. Its restricted additive extension applies componentwise when the same component correspondence and independent RHS unknowns are preserved.

This result is conditional: it does not yet prove that every rule in Section 5 can be compiled. That stronger claim requires a precise symbolic fragment and a proof that source alignment, refinement, and code generation always finish within it. A failure to compile is not evidence that no valid attributes exist.

Let $D(p)$ include the mathematical assumptions and any additional compilation restrictions. For a rule with written guard $C$, acceptance requires proving

$$
\operatorname{Legal}_L(p)\land C(p)
\Longrightarrow D(p)\land
\llbracket\widehat{\operatorname{check}}\rrbracket_p.
$$

Generating this check and proving that the guard implies it are separate tasks. The proof may remain unresolved even when the generated program is correct.

Compiling before matching fixes the program structure, allows shared expressions and simplification, and produces code usable by other rewrite engines. Runtime still processes metadata lists. Executing Section 5's constructor at each match remains a valid alternative; any performance advantage of compilation must be measured.

---

## Author notes

Before presenting this as a result of the implemented compiler:

- Define the supported symbolic fragment and prove termination of source alignment, group refinement, and code generation.
- Complete the preservation proofs for all group operations, ordering checks, and metadata translations. The identities above cover key steps, not the whole compiler.
- Confirm that the implementation follows this construction. If it chooses different valid attributes, prove validity preservation instead of exact equality with Section 5's builder.
- Validate the running example and compare generated programs with the direct metadata constructor. Include empty groups, interleaved axes, and infeasible ordering cases.

**Suggested bridge from Section 5:** The mathematical algorithm selects and orders logical axes for given metadata. The next section shows how symbolic mappings and partitioning express those choices before ranks are known, and how the compiler turns them into attribute programs.
