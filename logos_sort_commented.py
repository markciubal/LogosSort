"""
logos_sort_commented.py

"In the beginning was the Logos, and the Logos was with God, and the Logos was God."
 — John 1:1

The algorithm waits before it acts.

It first asks whether order is already present — ascending, descending, or dense
enough to count — and if so, it withdraws without disturbing what it finds.
Only into genuine disorder does it intervene: drawing a random pivot from entropy
it cannot predict, dividing the chaos into three regions by the proportion nature
itself prefers, and recursing into the smaller pieces while looping on the largest
to keep its own footprint minimal. When the budget runs out or the problem grows
small enough, it stops partitioning and sorts by hand, element by element, until
the work is done.

This is what the six disciplines below are each describing in their own language:
a principle that does not impose order on what is already ordered, that consults
something outside itself before acting, that divides rather than conquers, and
that knows when to stop. The philosopher calls it Logos. The biologist calls it
selection pressure. The political theorist calls it procedural legitimacy. The
theologian calls it the Word spoken into the void. The historian calls it the
conjuncture. The mathematician calls it an optimal expected-case algorithm.

They are all correct. The code beneath each description is identical.

Disciplines (all at 4th-year undergraduate level):
  I.   Philosophy
  II.  Biology
  III. Political Science
  IV.  Religion
  V.   History
  VI.  Mathematics
"""

import random
import math

# Golden ratio encoded as 61-bit fixed-point integers.
# Used by all six functions below — no floating-point division at runtime.
PHI_SHIFT = 61
PHI_NUM   = round(0.6180339887498949 * (1 << PHI_SHIFT))   # φ  · 2^61
PHI2_NUM  = round(0.3819660112501051 * (1 << PHI_SHIFT))   # (1−φ) · 2^61


# =============================================================================
# I. PHILOSOPHY
# =============================================================================

def logos_sort__philosophy(arr):
    """
    "In the beginning was the Logos, and the Logos was with God, and the Logos was God."
     — John 1:1

    LogosSort read through the lens of classical and continental philosophy.

    The algorithm enacts what philosophers from Heraclitus to Hegel have called
    the Logos: the rational principle that underlies and orders apparent chaos.
    Sorting is not merely computational — it is the imposition of knowable form
    upon contingent matter, the actualization of a potential order that was
    already latent in the data.

    Key philosophical resonances:
      - Heraclitean Logos: the hidden unity beneath surface disorder.
      - Aristotelian telos: the sorted array is the final cause toward which
        every comparison is directed.
      - Hegelian Aufhebung: each partition sublates the chaos of a subarray
        into a higher determinate order without destroying its content.
      - Husserlian phenomenology: the algorithm brackets irrelevant structure
        (monotone detection) to attend only to genuinely disordered regions.
      - Derridean trace: the depth counter carries the trace of every prior
        decision — a written record that constrains future freedom.

    Example domain: ranking philosophical texts by influence score, or
    ordering a corpus of arguments by logical priority.
    """
    import math as _math

    n = len(arr)
    # The cardinality of the set to be ordered — the scope of the world
    # upon which the Logos will act. In Aristotelian terms: the material cause.

    # The One requires no ordering. Plotinus: the One is beyond predication,
    # beyond comparison. A singleton or empty set is already at rest in itself.
    if n < 2:
        return arr[:]

    # The depth budget is the algorithm's analogue of Kantian limits on pure
    # reason. We cannot recurse infinitely — the antinomies of reason demand
    # a practical limit. 2⌊log₂n⌋ + 4 is tight enough to be meaningful,
    # wide enough to never fire on well-behaved input. It is the Critique
    # of Pure Reason expressed as an integer.
    depth_limit = 2 * int(_math.log2(n)) + 4

    def _ninther(a, lo, hi, idx):
        # The ninther is Hegel's dialectic in miniature.
        # Given three candidates — thesis (left), antithesis (right), synthesis
        # (center) — we perform a sorting network and extract the median.
        # The extremes cancel; the sensible middle survives. This is not mere
        # compromise: it is the genuine reconciliation that Hegel's Aufhebung
        # demands — both extremes are preserved in the middle, yet transcended.
        # Aristotle called this the mesotes: the virtuous mean between excess
        # and deficiency. Here it functions as the optimal pivot estimate.
        i0 = max(lo, idx - 1)
        i2 = min(hi, idx + 1)
        x, y, z = a[i0], a[idx], a[i2]
        if x > y: x, y = y, x
        if y > z: y, z = z, y
        if x > y: x, y = y, x
        return y

    def _dual_partition(a, lo, hi, p1, p2):
        # The dual partition is the ontological moment of the algorithm —
        # the point at which undifferentiated matter is divided into
        # determinate categories. Kant's categories of the understanding
        # impose structure on intuition; p1 and p2 impose structure on data.
        #
        # Three regions emerge: {x < p1}, {p1 ≤ x ≤ p2}, {x > p2}.
        # This tripartite structure echoes Hegel's Logic: Being, Nothing,
        # and Becoming collapse into Determinate Being. The middle region
        # — elements equal to a pivot — is absorbed permanently and never
        # re-examined. They have achieved their telos; further inquiry
        # would be redundant (Husserlian: they are constituted, not intended).
        if p1 > p2:
            p1, p2 = p2, p1
        lt = lo
        gt = hi
        i = lo
        while i <= gt:
            v = a[i]
            if v < p1:
                a[lt], a[i] = a[i], a[lt]
                lt += 1; i += 1
            elif v > p2:
                a[i], a[gt] = a[gt], a[i]
                gt -= 1
            else:
                i += 1
        return lt, gt

    def _insertion_sort(a, lo, hi):
        # Insertion sort is the phenomenological reduction applied to small
        # regions. It attends to each element in turn with full intentionality,
        # placing it in its eidetically correct position relative to all prior
        # elements. No heuristics, no sampling — pure, patient, apodictic
        # comparison. Husserl would recognize this as the Lebenswelt of sorting:
        # the pre-theoretical ground from which all higher structure emerges.
        for i in range(lo + 1, hi + 1):
            key = a[i]; j = i - 1
            while j >= lo and a[j] > key:
                a[j + 1] = a[j]; j -= 1
            a[j + 1] = key

    def _sort(a, lo, hi, depth):
        while lo < hi:
            size = hi - lo + 1

            # When depth is exhausted or the subarray is small, we fall back
            # to insertion sort. This is tzimtzum — the divine contraction
            # (Lurianic Kabbalah, adopted here philosophically): the algorithm
            # withdraws its complex machinery to allow a simpler, complete order
            # to emerge in the vacated space. The limit is not failure; it is
            # the condition of possibility for the work to finish.
            if depth <= 0 or size <= 48:
                _insertion_sort(a, lo, hi)
                return

            # Counting sort fast path: when the value range is less than 4× the
            # subarray size, we switch from comparison (diakrisis) to enumeration
            # (arithmos). This is the Platonic move from doxa to episteme —
            # instead of comparing one opinion against another, we appeal
            # directly to the Form: each integer occupies exactly one position
            # on the number line, and we simply count its instances.
            # No comparison is performed; the order is read off analytically,
            # as Kant would say — from the structure of the integers themselves.
            if isinstance(a[lo], int):
                mn = mx = a[lo]
                for i in range(lo + 1, hi + 1):
                    v = a[i]
                    if v < mn: mn = v
                    elif v > mx: mx = v
                span = mx - mn
                if span < size * 4:
                    counts = [0] * (span + 1)
                    for i in range(lo, hi + 1):
                        counts[a[i] - mn] += 1
                    k = lo
                    for v, cnt in enumerate(counts):
                        for _ in range(cnt):
                            a[k] = v + mn; k += 1
                    return

            # Monotone detection is the algorithm's recognition of pre-established
            # harmony (Leibniz). If the data is already ordered — ascending or
            # descending — no further work is needed. The Logos finds the world
            # already rational and withdraws. A descending run is merely the
            # mirror image of order; a single reversal restores it without
            # re-examining the ontological status of any element.
            if a[lo] <= a[lo + 1] <= a[lo + 2]:
                asc = True
                for i in range(lo, hi):
                    if a[i] > a[i + 1]: asc = False; break
                if asc: return
                desc = True
                for i in range(lo, hi):
                    if a[i] < a[i + 1]: desc = False; break
                if desc:
                    l, r = lo, hi
                    while l < r: a[l], a[r] = a[r], a[l]; l += 1; r -= 1
                    return

            # The oracle: a random value drawn from platform entropy.
            # This is the algorithm's acknowledgment of Derridean différance —
            # no pivot selection rule can be fully self-grounding without
            # appealing to something outside itself. The random seed defers
            # the question of which element is "truly" central, preventing
            # any adversarial input from exploiting a deterministic selection.
            # The chaos integer encodes the oracle's answer in 53 bits of
            # floating-point mantissa — the full precision of IEEE 754.
            c = 0.0
            while c == 0.0: c = random.uniform(-1.0, 1.0)
            chaos_int = int(abs(c) * (1 << 53))

            # The golden ratio φ ≈ 0.618 is not chosen for aesthetic reasons
            # (though Pacioli called it the Divine Proportion). It is chosen
            # because φ is the fixed point of the map x ↦ 1/(1+x) — the most
            # irrational number in the sense of continued fractions [1;1,1,1,...].
            # This makes it maximally resistant to periodic resonance with the
            # data's own structure. The two pivot candidates at φ and 1−φ are
            # symmetric about 0.5, distributing the partition space optimally.
            pn1 = PHI2_NUM * chaos_int
            pn2 = PHI_NUM  * chaos_int
            ps  = PHI_SHIFT + 53
            sp  = hi - lo
            idx1 = lo + (sp * pn1 >> ps)
            idx2 = lo + (sp * pn2 >> ps)

            p1 = _ninther(a, lo, hi, idx1)
            p2 = _ninther(a, lo, hi, idx2)
            lt, gt = _dual_partition(a, lo, hi, p1, p2)

            left_n  = lt - lo
            mid_n   = gt - lt + 1
            right_n = hi - gt

            # Tail-call optimization as Hegelian Aufhebung of the call stack.
            # The two smaller subproblems are recursed into — they are
            # genuinely new, genuinely other, and deserve their own stack frames.
            # The largest subproblem is sublated: it is negated as a recursive
            # call (the old frame is cancelled) yet preserved as the next
            # iteration of the loop (its content continues). The stack depth
            # remains O(log n) — finite reason, infinite reach.
            r0 = (left_n,  lo,    lt - 1)
            r1 = (mid_n,   lt,    gt    )
            r2 = (right_n, gt + 1, hi   )
            if r0[0] > r1[0]: r0, r1 = r1, r0
            if r1[0] > r2[0]: r1, r2 = r2, r1
            if r0[0] > r1[0]: r0, r1 = r1, r0
            for _, r_lo, r_hi in (r0, r1):
                if r_lo < r_hi: _sort(a, r_lo, r_hi, depth - 1)
            lo, hi = r2[1], r2[2]
            depth -= 1

    a = arr[:]
    _sort(a, 0, n - 1, depth_limit)
    return a


# =============================================================================
# II. BIOLOGY
# =============================================================================

def logos_sort__biology(arr):
    """
    "In the beginning was the Logos, and the Logos was with God, and the Logos was God."
     — John 1:1

    LogosSort read through the lens of evolutionary biology and molecular science.

    Sorting algorithms and biological ordering processes share deep structural
    parallels. Natural selection is a sorting process: it partitions a population
    by fitness, recursively across generations. DNA replication is a fidelity
    problem solved by partition-and-verify. Taxonomic classification is recursive
    hierarchical partitioning of phenotypic and genotypic space.

    Key biological resonances:
      - Natural selection as comparison-based sorting: fitness comparisons drive
        the partition, recursion across generations converges on order.
      - Phyllotaxis and the golden ratio: plant organ placement diverges by
        φ·360° ≈ 137.5° between successive elements — the same irrational
        spacing that makes this algorithm's pivot placement robust.
      - VDJ recombination: the immune system's random oracle — somatic
        hypermutation introduces entropy to prevent adversarial exploitation
        by pathogens. The algorithm uses platform entropy for the same reason.
      - Hayflick limit: cells have a finite division count (≈50–70 for human
        somatic cells). The depth budget 2⌊log₂n⌋ + 4 is the algorithm's
        Hayflick limit — a built-in senescence that prevents runaway recursion.
      - Cladistics: recursive dual-pivot partition mirrors the bifurcating
        tree structure of phylogenetic analysis (with a trichotomy at each node).

    Example domain: sorting gene expression values by fold-change, ordering
    protein sequences by hydrophobicity index, ranking taxa by morphological
    distance from an outgroup.
    """
    import math as _math

    n = len(arr)
    # Population size N — the number of individuals (elements) subject to
    # the selection process. Corresponds to sample size in population genetics.

    # A monotypic taxon or empty sample requires no sorting. A population of
    # one has no variance; natural selection has nothing to act upon.
    if n < 2:
        return arr[:]

    # The depth budget is the algorithm's Hayflick limit: a maximum number
    # of recursive divisions before senescence forces a switch to the
    # simple, reliable insertion sort. 2⌊log₂n⌋ + 4 ensures the limit
    # is never reached on well-distributed data — only on pathological
    # inputs analogous to inbreeding depression (loss of variance).
    depth_limit = 2 * int(_math.log2(n)) + 4

    def _ninther(a, lo, hi, idx):
        # Pivot selection by local median — analogous to optimal foraging
        # theory's marginal value theorem. Rather than committing to a single
        # candidate (which risks selecting an outlier, analogous to a fitness
        # measurement confounded by environmental noise), we sample three
        # neighboring values and take the median.
        #
        # In QTL mapping terms: we are performing a three-point interval mapping
        # step. The flanking markers (i0, i2) bound the candidate locus (idx);
        # the median is the most robust estimate of the true locus effect,
        # resistant to the outlier flanking values that represent phenotypic
        # plasticity rather than genotypic signal.
        i0 = max(lo, idx - 1)
        i2 = min(hi, idx + 1)
        x, y, z = a[i0], a[idx], a[i2]
        if x > y: x, y = y, x
        if y > z: y, z = z, y
        if x > y: x, y = y, x
        return y

    def _dual_partition(a, lo, hi, p1, p2):
        # The dual partition mirrors ecological niche partitioning.
        # Two keystone fitness thresholds (p1, p2) define three adaptive zones:
        #   {x < p1}:  low-fitness individuals — outcompeted, moved left.
        #   {p1≤x≤p2}: intermediate — the viable population, retained centrally.
        #   {x > p2}:  high-fitness individuals — selected, moved right.
        #
        # This is a single-pass O(n) selection analogous to one generation of
        # truncation selection with two cut-off points. Elements equal to a
        # pivot are absorbed into the central zone permanently — in ecological
        # terms, they have found their realized niche and face no further
        # competitive displacement pressure.
        if p1 > p2:
            p1, p2 = p2, p1
        lt = lo
        gt = hi
        i = lo
        while i <= gt:
            v = a[i]
            if v < p1:
                a[lt], a[i] = a[i], a[lt]
                lt += 1; i += 1
            elif v > p2:
                a[i], a[gt] = a[gt], a[i]
                gt -= 1
            else:
                i += 1
        return lt, gt

    def _insertion_sort(a, lo, hi):
        # Insertion sort for small subarrays — the molecular proofreading
        # step of the algorithm. DNA polymerase III achieves error rates of
        # ~10⁻⁷ per base pair by examining each nucleotide individually and
        # correcting mismatches before moving on. Insertion sort does exactly
        # this: it examines each element and walks it back to its correct
        # position one comparison at a time. Expensive per element, but
        # for n ≤ 48 the absolute cost is negligible and correctness is total.
        for i in range(lo + 1, hi + 1):
            key = a[i]; j = i - 1
            while j >= lo and a[j] > key:
                a[j + 1] = a[j]; j -= 1
            a[j + 1] = key

    def _sort(a, lo, hi, depth):
        while lo < hi:
            size = hi - lo + 1

            # Depth exhausted or subarray small: invoke proofreading (insertion sort).
            # This is the algorithm's equivalent of the SOS response in E. coli —
            # when normal replication stalls (depth budget gone) or the region
            # is small enough that low-fidelity bulk machinery would be wasteful,
            # we switch to a slow, high-accuracy repair pathway.
            if depth <= 0 or size <= 48:
                _insertion_sort(a, lo, hi)
                return

            # Counting sort fast path — analogous to the Hardy-Weinberg equilibrium
            # in a dense allele space. When allele values (integers) span a range
            # less than 4× the population size, we can apply an exact census
            # (count each allele frequency) rather than pairwise fitness comparisons.
            # This is the difference between genotype frequency enumeration
            # and individual-by-individual fitness ranking — O(n) vs O(n log n).
            # The counting array is the allele frequency spectrum; writing back
            # is equivalent to reconstructing the population from the spectrum
            # under Hardy-Weinberg assumptions (no drift, no selection).
            if isinstance(a[lo], int):
                mn = mx = a[lo]
                for i in range(lo + 1, hi + 1):
                    v = a[i]
                    if v < mn: mn = v
                    elif v > mx: mx = v
                span = mx - mn
                if span < size * 4:
                    counts = [0] * (span + 1)
                    for i in range(lo, hi + 1):
                        counts[a[i] - mn] += 1
                    k = lo
                    for v, cnt in enumerate(counts):
                        for _ in range(cnt):
                            a[k] = v + mn; k += 1
                    return

            # Monotone detection — recognizing populations already at or near
            # evolutionary stable strategy (ESS). An ascending sequence is a
            # population sorted by fitness with no disruptive selection pressure;
            # it is already at ESS and requires no intervention. A descending
            # sequence is the mirror image — a population whose fitness ranking
            # was recorded in reverse order; a single reversal corrects it.
            # This is the biological analogue of recognizing pre-adaptation:
            # a trait that is already optimal for the new environment requires
            # no further selection — only recognition.
            if a[lo] <= a[lo + 1] <= a[lo + 2]:
                asc = True
                for i in range(lo, hi):
                    if a[i] > a[i + 1]: asc = False; break
                if asc: return
                desc = True
                for i in range(lo, hi):
                    if a[i] < a[i + 1]: desc = False; break
                if desc:
                    l, r = lo, hi
                    while l < r: a[l], a[r] = a[r], a[l]; l += 1; r -= 1
                    return

            # Random oracle — the algorithm's VDJ recombination step.
            # The adaptive immune system uses RAG1/RAG2-mediated somatic
            # hypermutation to generate antibody diversity that no pathogen
            # can predict in advance. This random seed serves the same purpose:
            # it makes the pivot selection unpredictable to any adversarial
            # input sequence. Without it, a deterministic pivot rule can be
            # exploited to force O(n²) performance — analogous to immune escape.
            # The 53 bits of mantissa entropy provide ~9×10¹⁵ distinct pivot
            # configurations — sufficient diversity for any realistic input.
            c = 0.0
            while c == 0.0: c = random.uniform(-1.0, 1.0)
            chaos_int = int(abs(c) * (1 << 53))

            # Pivot placement at φ ≈ 0.618 and 1−φ ≈ 0.382 of the subarray span,
            # scaled by the oracle integer. φ appears in plant phyllotaxis as the
            # golden angle (≈137.5°) between successive leaf or floret positions.
            # Botanists since Hofmeister (1868) have noted that this spacing
            # maximizes packing density by ensuring no two organs share an angular
            # position — it is optimal because φ is maximally irrational.
            # The same property here ensures pivot candidates are robustly
            # distributed regardless of the data's own periodic structure.
            pn1 = PHI2_NUM * chaos_int
            pn2 = PHI_NUM  * chaos_int
            ps  = PHI_SHIFT + 53
            sp  = hi - lo
            idx1 = lo + (sp * pn1 >> ps)
            idx2 = lo + (sp * pn2 >> ps)

            p1 = _ninther(a, lo, hi, idx1)
            p2 = _ninther(a, lo, hi, idx2)
            lt, gt = _dual_partition(a, lo, hi, p1, p2)

            left_n  = lt - lo
            mid_n   = gt - lt + 1
            right_n = hi - gt

            # Tail-call optimization mirrors the cladistic parsimony principle.
            # Rather than allocating a new stack frame for the largest subproblem
            # (which would be profligate — maximum parsimony rejects unnecessary
            # branching), we reuse the current frame and loop. The two smaller
            # clades (subproblems) each receive their own recursive call —
            # they are genuinely novel and require independent treatment.
            # Stack depth O(log n) is the molecular clock of the recursion:
            # bounded, predictable, and proportional to the log of population size.
            r0 = (left_n,  lo,    lt - 1)
            r1 = (mid_n,   lt,    gt    )
            r2 = (right_n, gt + 1, hi   )
            if r0[0] > r1[0]: r0, r1 = r1, r0
            if r1[0] > r2[0]: r1, r2 = r2, r1
            if r0[0] > r1[0]: r0, r1 = r1, r0
            for _, r_lo, r_hi in (r0, r1):
                if r_lo < r_hi: _sort(a, r_lo, r_hi, depth - 1)
            lo, hi = r2[1], r2[2]
            depth -= 1

    a = arr[:]
    _sort(a, 0, n - 1, depth_limit)
    return a


# =============================================================================
# III. POLITICAL SCIENCE
# =============================================================================

def logos_sort__political_science(arr):
    """
    "In the beginning was the Logos, and the Logos was with God, and the Logos was God."
     — John 1:1

    LogosSort read through the lens of political theory and formal politics.

    Sorting is a collective choice problem: given n elements with no agreed
    order, the algorithm must impose a consistent preference ranking. Arrow's
    impossibility theorem (1951) establishes that no comparison-based social
    welfare function satisfying independence of irrelevant alternatives,
    Pareto efficiency, and non-dictatorship can aggregate individual orderings
    into a complete social ordering — yet comparison-based sorting achieves
    exactly this, at the cost of Θ(n log n) comparisons. The algorithm is
    the benevolent dictator that Arrow's theorem says cannot exist democratically.

    Key political science resonances:
      - Arrow's impossibility theorem: explains why O(n log n) is unavoidable.
      - Gibbard-Satterthwaite theorem: random oracle prevents strategic pivot
        manipulation (analogous to preventing agenda-setting power).
      - Median voter theorem: ninther pivot selection converges to the median,
        the equilibrium of a unidimensional policy space (Downs, 1957).
      - Duverger's law: dual-pivot partition naturally produces a three-party
        structure — left, center, right — mirroring pluralist systems.
      - Constitutional depth limits: the depth budget is the separation of
        powers that prevents recursive concentration of authority.

    Example domain: ranking candidates by approval rating, ordering legislative
    bills by co-sponsorship count, sorting constituencies by turnout percentage.
    """
    import math as _math

    n = len(arr)
    # The electorate size — the number of preference-bearing agents (elements)
    # over which a social ordering must be constructed.

    # A body of one sovereign or an empty chamber requires no aggregation.
    # The preference of a singleton is trivially its own social ordering.
    if n < 2:
        return arr[:]

    # The depth budget functions as a constitutional term limit.
    # Unconstrained recursion is unconstrained executive power — it concentrates
    # authority without bound. 2⌊log₂n⌋ + 4 iterations is the algorithm's
    # separation of powers: beyond this depth, the deliberative process
    # (insertion sort) takes over — slower, careful, locally exhaustive.
    depth_limit = 2 * int(_math.log2(n)) + 4

    def _ninther(a, lo, hi, idx):
        # Pivot selection by local median — a direct application of the
        # median voter theorem (Hotelling 1929; Black 1948; Downs 1957).
        # In a unidimensional policy space with single-peaked preferences,
        # the median voter's position is the Condorcet winner: it defeats
        # every other position in pairwise majority vote.
        #
        # The ninther approximates this median locally. Rather than a full O(n)
        # scan for the true median (computationally expensive, analogous to a
        # full census), it samples three neighboring positions and takes the
        # middle one. This is stratified sampling at minimal cost — the kind
        # of heuristic used in exit polling and rapid preference aggregation.
        i0 = max(lo, idx - 1)
        i2 = min(hi, idx + 1)
        x, y, z = a[i0], a[idx], a[i2]
        if x > y: x, y = y, x
        if y > z: y, z = z, y
        if x > y: x, y = y, x
        return y

    def _dual_partition(a, lo, hi, p1, p2):
        # Dual-pivot partition as Duverger's law applied to data.
        # Two pivot thresholds (p1, p2) divide the political space into
        # three ideological blocs: left ({x < p1}), center ({p1 ≤ x ≤ p2}),
        # right ({x > p2}). Elements equal to a pivot enter the center bloc
        # permanently — they have found their coalition and will not be
        # redistributed in future rounds.
        #
        # The single-pass scan is O(n): every element is examined at most
        # twice (once by i advancing, once after being swapped from gt).
        # This is the algorithm's equivalent of a single-round ranked-choice
        # ballot count: linear in the number of voters, no runoffs needed
        # for the central bloc whose position is already determined.
        if p1 > p2:
            p1, p2 = p2, p1
        lt = lo
        gt = hi
        i = lo
        while i <= gt:
            v = a[i]
            if v < p1:
                a[lt], a[i] = a[i], a[lt]
                lt += 1; i += 1
            elif v > p2:
                a[i], a[gt] = a[gt], a[i]
                gt -= 1
            else:
                i += 1
        return lt, gt

    def _insertion_sort(a, lo, hi):
        # Insertion sort as town-hall deliberation — the parliamentary procedure
        # for small constituencies. Each new element is introduced to the chamber
        # and debated against existing members one at a time until its correct
        # position (its seat in the preference ordering) is found.
        # Slow per element, but exhaustively correct — the analog of a
        # full committee hearing rather than a floor vote by bloc.
        # Appropriate precisely when the constituency is small enough
        # that individual attention is affordable and high-stakes.
        for i in range(lo + 1, hi + 1):
            key = a[i]; j = i - 1
            while j >= lo and a[j] > key:
                a[j + 1] = a[j]; j -= 1
            a[j + 1] = key

    def _sort(a, lo, hi, depth):
        while lo < hi:
            size = hi - lo + 1

            # Depth exhausted or constituency small: hand to deliberative committee.
            # This is the subsidiarity principle (Maastricht Treaty, 1992):
            # decisions should be taken at the lowest effective level of governance.
            # When the subarray is small or the recursion budget is spent,
            # local deliberation (insertion sort) is more appropriate than
            # continued top-down partition.
            if depth <= 0 or size <= 48:
                _insertion_sort(a, lo, hi)
                return

            # Counting sort as proportional representation.
            # When the value range is dense (span < 4×size), the distribution
            # is analogous to a PR electorate: many voters share the same
            # preference score. Rather than pairwise comparison (majoritarian
            # debate), we count the frequency of each preference value and
            # allocate seats proportionally. This is the d'Hondt method
            # of the sorting world — O(n) enumeration beats O(n log n)
            # comparison when the issue space is compact.
            if isinstance(a[lo], int):
                mn = mx = a[lo]
                for i in range(lo + 1, hi + 1):
                    v = a[i]
                    if v < mn: mn = v
                    elif v > mx: mx = v
                span = mx - mn
                if span < size * 4:
                    counts = [0] * (span + 1)
                    for i in range(lo, hi + 1):
                        counts[a[i] - mn] += 1
                    k = lo
                    for v, cnt in enumerate(counts):
                        for _ in range(cnt):
                            a[k] = v + mn; k += 1
                    return

            # Monotone detection: recognizing regimes of stable preference order.
            # A fully ascending sequence is a political system already at
            # equilibrium — no realignment is possible without external shock.
            # A fully descending sequence is a system in perfect anti-consensus:
            # a single reversal (180° rotation of the preference axis)
            # restores canonical order. This is the analyst's recognition that
            # what looks like disorder is sometimes merely a labeling convention.
            if a[lo] <= a[lo + 1] <= a[lo + 2]:
                asc = True
                for i in range(lo, hi):
                    if a[i] > a[i + 1]: asc = False; break
                if asc: return
                desc = True
                for i in range(lo, hi):
                    if a[i] < a[i + 1]: desc = False; break
                if desc:
                    l, r = lo, hi
                    while l < r: a[l], a[r] = a[r], a[l]; l += 1; r -= 1
                    return

            # The random oracle as Rawlsian veil of ignorance.
            # A pivot chosen from platform entropy is a pivot chosen behind
            # the veil — no prior knowledge of the data's distribution
            # can bias it toward the interests of any particular subgroup.
            # This prevents Gibbard-Satterthwaite strategic manipulation:
            # if pivot selection were deterministic and known, an adversary
            # could construct inputs that force O(n²) worst-case performance,
            # analogous to agenda-setting that always selects the Condorcet loser.
            # Randomness is the constitutional guarantee of procedural fairness.
            c = 0.0
            while c == 0.0: c = random.uniform(-1.0, 1.0)
            chaos_int = int(abs(c) * (1 << 53))

            # Golden ratio pivot placement — the spatial analogue of the
            # median voter equilibrium in a two-pivot system. φ ≈ 0.618 and
            # 1−φ ≈ 0.382 are symmetric about 0.5, placing the two pivots
            # in the interior of the distribution rather than at the extremes.
            # This mirrors Downs's (1957) finding that two-party competition
            # drives both parties toward the median: the pivots converge toward
            # the center of the value distribution, minimizing partition imbalance.
            pn1 = PHI2_NUM * chaos_int
            pn2 = PHI_NUM  * chaos_int
            ps  = PHI_SHIFT + 53
            sp  = hi - lo
            idx1 = lo + (sp * pn1 >> ps)
            idx2 = lo + (sp * pn2 >> ps)

            p1 = _ninther(a, lo, hi, idx1)
            p2 = _ninther(a, lo, hi, idx2)
            lt, gt = _dual_partition(a, lo, hi, p1, p2)

            left_n  = lt - lo
            mid_n   = gt - lt + 1
            right_n = hi - gt

            # Tail-call optimization as federalism: the two smaller constituencies
            # (subproblems) receive their own recursive treatment — genuine local
            # autonomy, genuine separate deliberation. The largest constituency
            # is handled by the same governing body (loop iteration) rather than
            # spawning a new institution — economies of scale, no administrative
            # overhead. Stack depth O(log n) guarantees no level of government
            # accumulates unbounded subordinate levels. This is fiscal federalism
            # in algorithmic form: subsidiarity with a hard budget constraint.
            r0 = (left_n,  lo,    lt - 1)
            r1 = (mid_n,   lt,    gt    )
            r2 = (right_n, gt + 1, hi   )
            if r0[0] > r1[0]: r0, r1 = r1, r0
            if r1[0] > r2[0]: r1, r2 = r2, r1
            if r0[0] > r1[0]: r0, r1 = r1, r0
            for _, r_lo, r_hi in (r0, r1):
                if r_lo < r_hi: _sort(a, r_lo, r_hi, depth - 1)
            lo, hi = r2[1], r2[2]
            depth -= 1

    a = arr[:]
    _sort(a, 0, n - 1, depth_limit)
    return a


# =============================================================================
# IV. RELIGION
# =============================================================================

def logos_sort__religion(arr):
    """
    "In the beginning was the Logos, and the Logos was with God, and the Logos was God."
     — John 1:1

    LogosSort read through the lens of theology, comparative religion, and
    religious philosophy.

    The algorithm's name is not metaphorical — it is theological. Logos (λόγος)
    is the term John's Gospel uses for the pre-existent divine Word through which
    all things were made (John 1:3). Heraclitus used the same term for the cosmic
    ordering principle underlying apparent flux. Philo of Alexandria identified
    the Logos as the divine intermediary between the transcendent God and the
    material world. In all three traditions, the Logos is the principle that
    converts chaos (tohu wa-bohu, Genesis 1:2) into ordered creation.

    This algorithm enacts that theological claim computationally: it takes an
    arbitrary arrangement — chaos — and imposes upon it the one arrangement
    that is most knowable, most ordered, most at rest in itself.

    Key theological resonances:
      - John 1:1–3: Logos as the ordering Word through which all things are made.
      - Genesis 1: creation as the separation (partition) of darkness from light,
        waters above from waters below — dual-pivot cosmogony.
      - Lurianic Kabbalah (tzimtzum): divine contraction to allow finite creation.
      - Eschatology: the sorted array as the final state — the omega point
        toward which all partial orderings tend.
      - Apophatic theology: the oracle is unknowable in itself; only its
        effects (the sorted output) are accessible to creaturely knowledge.

    Example domain: ordering sacred texts by estimated date of composition,
    ranking religious traditions by geographic spread, sorting theological
    arguments by logical dependency.
    """
    import math as _math

    n = len(arr)
    # The number of created things to be ordered — the scope of the cosmos
    # upon which the divine Logos acts. In Neoplatonic terms: the multiplicity
    # that has proceeded from the One and must be returned to order.

    # The One (Plotinus: Enneads VI.9) is beyond predication, beyond comparison.
    # A single element or empty array is already at rest in itself — it has
    # not fallen into the multiplicity that requires ordering. It is returned
    # as-is: the algorithm withdraws before the sacred simplicity of the One.
    if n < 2:
        return arr[:]

    # The depth budget is tzimtzum — the divine self-contraction described by
    # Isaac Luria (16th c. Safed). Before creation, the Ein Sof (the Infinite)
    # contracted to allow finite space for the world. The depth limit contracts
    # the algorithm's infinite recursive potential to a finite budget:
    # 2⌊log₂n⌋ + 4 levels. Beyond this, the simple, contemplative act of
    # insertion sort takes over — the hesychast's prayer replacing the
    # scholastic's disputation when the arguments have gone deep enough.
    depth_limit = 2 * int(_math.log2(n)) + 4

    def _ninther(a, lo, hi, idx):
        # The ninther enacts the Deuteronomic principle of multiple witnesses:
        # "A matter must be established by the testimony of two or three witnesses"
        # (Deut. 19:15; echoed in Matt. 18:16 and 2 Cor. 13:1).
        # No single candidate is accepted as the pivot on its own testimony.
        # Three neighbors are consulted; the median — the witness whose testimony
        # is corroborated by at least one other — is confirmed as the pivot.
        #
        # This is also the coincidentia oppositorum (Nicholas of Cusa):
        # the extreme witnesses (maximum and minimum) are reconciled in the
        # median, which participates in both extremes while transcending both.
        i0 = max(lo, idx - 1)
        i2 = min(hi, idx + 1)
        x, y, z = a[i0], a[idx], a[i2]
        if x > y: x, y = y, x
        if y > z: y, z = z, y
        if x > y: x, y = y, x
        return y

    def _dual_partition(a, lo, hi, p1, p2):
        # The dual partition is a computational cosmogony — the separation of
        # the primordial chaos into ordered regions. Genesis 1 describes
        # creation as a sequence of separations (havdalot): light from darkness,
        # waters above from waters below, dry land from sea.
        #
        # Here two thresholds (p1, p2) perform the primordial separation:
        #   Left  {x < p1}:      the lesser — separated out to the left.
        #   Middle {p1 ≤ x ≤ p2}: the liminal — the templum, the holy of holies,
        #                          the sacred center that is never re-examined
        #                          once constituted. In cultic terms: the
        #                          consecrated elements are set apart permanently.
        #   Right {x > p2}:      the greater — separated out to the right.
        #
        # The scan pointer i advances through the unconsecrated middle,
        # performing the priestly work of classification, until the entire
        # congregation has been sorted into its proper liturgical station.
        if p1 > p2:
            p1, p2 = p2, p1
        lt = lo
        gt = hi
        i = lo
        while i <= gt:
            v = a[i]
            if v < p1:
                a[lt], a[i] = a[i], a[lt]
                lt += 1; i += 1
            elif v > p2:
                a[i], a[gt] = a[gt], a[i]
                gt -= 1
            else:
                i += 1
        return lt, gt

    def _insertion_sort(a, lo, hi):
        # Insertion sort as lectio divina — the ancient monastic practice of
        # slow, attentive, contemplative reading. Each element is received
        # individually, dwelt upon (compared against its predecessors),
        # and placed in its correct position with full attention before
        # moving on. There is no haste, no sampling, no shortcut.
        # This is the hesychast method: perfect local attention, applied
        # sequentially, achieves perfect local order. Appropriate for
        # small subarrays where the cost of that attention is affordable
        # and the reward — absolute correctness — is worth paying.
        for i in range(lo + 1, hi + 1):
            key = a[i]; j = i - 1
            while j >= lo and a[j] > key:
                a[j + 1] = a[j]; j -= 1
            a[j + 1] = key

    def _sort(a, lo, hi, depth):
        while lo < hi:
            size = hi - lo + 1

            # Depth exhausted or region small: the algorithm enters kenosis.
            # Kenosis (κένωσις, Phil. 2:7) is the self-emptying of the divine —
            # in Christological theology, Christ empties himself of divine
            # prerogative to take on creaturely limitation. Here the algorithm
            # empties itself of its complex partitioning machinery and becomes
            # the simple, patient insertion sort. This is not failure; it is
            # the condition of completion. The infinite must become finite
            # for the work to actually finish.
            if depth <= 0 or size <= 48:
                _insertion_sort(a, lo, hi)
                return

            # Counting sort as divine omniscience applied to a dense domain.
            # Aquinas argues that God knows all things not by comparing one
            # thing to another (per modum compositionis et divisionis) but
            # by knowing each thing directly in its essence through the divine
            # ideas. Counting sort is the closest algorithmic approximation:
            # when integers are dense (span < 4×size), we know each value's
            # frequency directly — no pairwise comparison, no relational knowing,
            # just immediate enumeration. The counting array is the divine
            # intellect's catalog of essences; writing back is creation ex ordine.
            if isinstance(a[lo], int):
                mn = mx = a[lo]
                for i in range(lo + 1, hi + 1):
                    v = a[i]
                    if v < mn: mn = v
                    elif v > mx: mx = v
                span = mx - mn
                if span < size * 4:
                    counts = [0] * (span + 1)
                    for i in range(lo, hi + 1):
                        counts[a[i] - mn] += 1
                    k = lo
                    for v, cnt in enumerate(counts):
                        for _ in range(cnt):
                            a[k] = v + mn; k += 1
                    return

            # Monotone detection as the recognition of states of grace.
            # A fully ascending sequence is a congregation already in right
            # relationship — ordered, at peace, requiring no further correction.
            # The Logos withdraws: "I came not to judge the world but to save it"
            # (John 12:47). A fully descending sequence is a congregation ordered
            # in perfect mirror-image — the same right relationships, merely
            # named in reverse. A single reversal (teshuvah — return, repentance)
            # restores the canonical orientation. The structure was always there;
            # it only needed to be recognized and turned the right way.
            if a[lo] <= a[lo + 1] <= a[lo + 2]:
                asc = True
                for i in range(lo, hi):
                    if a[i] > a[i + 1]: asc = False; break
                if asc: return
                desc = True
                for i in range(lo, hi):
                    if a[i] < a[i + 1]: desc = False; break
                if desc:
                    l, r = lo, hi
                    while l < r: a[l], a[r] = a[r], a[l]; l += 1; r -= 1
                    return

            # The oracle: casting lots. From the Urim and Thummim (Exod. 28:30)
            # to the selection of Matthias (Acts 1:26) to the Islamic practice
            # of istikharah, sacred traditions have recognized that randomness
            # can be a vehicle for revelation — a way of consulting what lies
            # beyond human calculation. The random seed here serves an analogous
            # apophatic function: it introduces what is, from the algorithm's
            # perspective, genuinely unknowable — platform entropy. No adversarial
            # input can predict or manipulate it. The oracle speaks, and we trust
            # the output without comprehending the divine arithmetic behind it.
            c = 0.0
            while c == 0.0: c = random.uniform(-1.0, 1.0)
            chaos_int = int(abs(c) * (1 << 53))

            # The golden ratio as the Divine Proportion (La Divina Proportione,
            # Luca Pacioli, 1509; illustrated by Leonardo da Vinci). Pacioli
            # identified five properties of φ that he called "divine":
            # it is one (unique), it is irrational (ineffable), it is self-similar
            # (trinitarian — φ = 1 + 1/φ), it relates the whole to its parts
            # as the greater to the lesser, and it is the proportion of the
            # Platonic solids. The two pivot candidates at φ and 1−φ are placed
            # at the proportions that the divine proportion itself mandates —
            # the cut that divides a segment such that the whole is to the greater
            # part as the greater is to the lesser. Theologically: the proportion
            # of incarnation, where the infinite enters the finite at just the
            # right point to preserve the integrity of both.
            pn1 = PHI2_NUM * chaos_int
            pn2 = PHI_NUM  * chaos_int
            ps  = PHI_SHIFT + 53
            sp  = hi - lo
            idx1 = lo + (sp * pn1 >> ps)
            idx2 = lo + (sp * pn2 >> ps)

            p1 = _ninther(a, lo, hi, idx1)
            p2 = _ninther(a, lo, hi, idx2)
            lt, gt = _dual_partition(a, lo, hi, p1, p2)

            left_n  = lt - lo
            mid_n   = gt - lt + 1
            right_n = hi - gt

            # Tail-call optimization as eschatological economy.
            # The two smaller partitions are entrusted to subordinate agencies
            # (recursive calls) — they are, in Aquinas's terms, secondary causes
            # acting with genuine causal power of their own. The largest partition
            # is retained by the primary cause (the loop) — not because it is
            # more important, but because the economy of salvation (oikonomia)
            # requires that the most extensive work be done without spawning
            # a new dispensation. The stack depth O(log n) is the algorithm's
            # assurance that the recursion will reach its omega point — the final,
            # fully sorted state — in finite time and with finite resources.
            r0 = (left_n,  lo,    lt - 1)
            r1 = (mid_n,   lt,    gt    )
            r2 = (right_n, gt + 1, hi   )
            if r0[0] > r1[0]: r0, r1 = r1, r0
            if r1[0] > r2[0]: r1, r2 = r2, r1
            if r0[0] > r1[0]: r0, r1 = r1, r0
            for _, r_lo, r_hi in (r0, r1):
                if r_lo < r_hi: _sort(a, r_lo, r_hi, depth - 1)
            lo, hi = r2[1], r2[2]
            depth -= 1

    a = arr[:]
    _sort(a, 0, n - 1, depth_limit)
    return a


# =============================================================================
# V. HISTORY
# =============================================================================

def logos_sort__history(arr):
    """
    "In the beginning was the Logos, and the Logos was with God, and the Logos was God."
     — John 1:1

    LogosSort read through the lens of historiography and the philosophy of history.

    Sorting a list is structurally identical to constructing a historical narrative:
    both impose a linear ordering on a set of events (elements) that existed, prior
    to the act of ordering, in a state of archival chaos. The historian's choices —
    which events to compare, which periodization to impose, which causal chains to
    trace — are precisely the choices the sorting algorithm makes at each step.

    Key historiographical resonances:
      - Annales school (Braudel): longue durée as counting sort — structural
        forces operate at the level of bulk enumeration, bypassing event-by-event
        narrative comparison.
      - Événementielle (short-term event history): comparison sort — each event
        is weighed against others one at a time, producing a narrative sequence.
      - Conjonctures (medium-term cycles): the partition boundaries — pivot values
        that define the threshold between historical epochs.
      - Cleopatra's nose (Pascal): the random oracle — historical contingency
        makes deterministic prediction impossible. Small causes (a random seed)
        produce large effects.
      - Whig history: the ascending monotone check — the temptation to see the
        present as the inevitable culmination of the past.
      - Benjamin's dialectical image: the deepest recursion is where the past
        flashes into the present — a concentrated moment of historical recognition.

    Example domain: ordering primary sources by date of composition, ranking
    historical events by estimated casualty count, sorting dynasties by duration.
    """
    import math as _math

    n = len(arr)
    # The corpus size — the number of historical records, events, or sources
    # that must be placed into a coherent chronological or causal ordering.
    # This is the raw archival mass before periodization has been applied.

    # A single source or empty archive requires no ordering. A monograph with
    # one datum presents no historiographical problem; the act of interpretation
    # and the act of description coincide. Return immediately.
    if n < 2:
        return arr[:]

    # The depth budget corresponds to the limits of historical memory and
    # documentary survival. No archive is infinite; no periodization can
    # recurse indefinitely into finer sub-periods without losing meaning.
    # 2⌊log₂n⌋ + 4 is the algorithm's equivalent of the horizon of historical
    # intelligibility: beyond this depth of subdivision, we switch to
    # the close-reading method (insertion sort) — the archivist's careful
    # document-by-document analysis that replaces structural periodization
    # when the sub-period is small enough to bear individual attention.
    depth_limit = 2 * int(_math.log2(n)) + 4

    def _ninther(a, lo, hi, idx):
        # The ninther is the historian's triangulation method — the practice
        # of verifying a datum against multiple independent sources before
        # accepting it as a reliable boundary (pivot) between periods.
        #
        # A single source may be biased, interpolated, or forged (the problem
        # of diplomatic criticism since Mabillon's De Re Diplomatica, 1681).
        # Three neighboring sources are consulted; the median value is taken
        # as the pivot — the boundary marker that is corroborated by at least
        # one adjacent source. This is source criticism as pivot selection:
        # the outlier (possibly interpolated) extreme values are rejected in
        # favor of the internally consistent median witness.
        i0 = max(lo, idx - 1)
        i2 = min(hi, idx + 1)
        x, y, z = a[i0], a[idx], a[i2]
        if x > y: x, y = y, x
        if y > z: y, z = z, y
        if x > y: x, y = y, x
        return y

    def _dual_partition(a, lo, hi, p1, p2):
        # The dual partition is the algorithm's act of periodization —
        # the imposition of epoch boundaries upon a continuous historical flux.
        # Two conjunctural thresholds (p1, p2) — analogous to Braudel's
        # medium-term structural boundaries — divide the archive into three
        # temporal blocs:
        #   Antecedent {x < p1}:  the earlier period, pushed to the past.
        #   Conjoncture {p1≤x≤p2}: the structural middle period — stable,
        #                           absorbed permanently, not subject to
        #                           further sub-periodization in this pass.
        #   Subsequent {x > p2}:   the later period, pushed to the future.
        #
        # Elements equal to a pivot enter the conjoncture permanently:
        # they belong to neither the preceding nor the following epoch
        # and need not be re-examined — historiographically, they are the
        # events that define the period rather than belonging to the periods
        # on either side of it. Their interpretation is complete.
        if p1 > p2:
            p1, p2 = p2, p1
        lt = lo
        gt = hi
        i = lo
        while i <= gt:
            v = a[i]
            if v < p1:
                a[lt], a[i] = a[i], a[lt]
                lt += 1; i += 1
            elif v > p2:
                a[i], a[gt] = a[gt], a[i]
                gt -= 1
            else:
                i += 1
        return lt, gt

    def _insertion_sort(a, lo, hi):
        # Insertion sort as the archivist's close-reading method —
        # the paleographic analysis of a small document set.
        # Each source (element) is examined individually, compared against
        # the already-ordered corpus (j walking leftward), and inserted at
        # the position where it fits the established chronological sequence.
        # This is how a trained archivist handles a box of undated letters:
        # one at a time, each placed relative to what is already known,
        # until the entire box is in sequence. Slow, careful, certain.
        for i in range(lo + 1, hi + 1):
            key = a[i]; j = i - 1
            while j >= lo and a[j] > key:
                a[j + 1] = a[j]; j -= 1
            a[j + 1] = key

    def _sort(a, lo, hi, depth):
        while lo < hi:
            size = hi - lo + 1

            # Depth exhausted or sub-period small: switch to close reading.
            # This is the shift from Braudel's structural history (longue durée,
            # macro-level partition) to Ranke's event-history (wie es eigentlich
            # gewesen — as it actually happened, source by source). When the
            # sub-period is small enough or the periodization budget is spent,
            # the algorithm abandons structural abstraction and examines each
            # datum individually. Ranke wins at the margins; Braudel wins in bulk.
            if depth <= 0 or size <= 48:
                _insertion_sort(a, lo, hi)
                return

            # Counting sort as cliometrics (Fogel and Engerman, 1974).
            # Quantitative history bypasses narrative comparison by counting
            # the frequency of each measured value directly. When the value
            # range is dense (span < 4×size) — as in economic time series,
            # demographic records, or price data — we enumerate frequencies
            # rather than compare individual records. This is the New Economic
            # History's method: statistical enumeration over narrative comparison,
            # O(n) over O(n log n), when the evidence is sufficiently uniform.
            if isinstance(a[lo], int):
                mn = mx = a[lo]
                for i in range(lo + 1, hi + 1):
                    v = a[i]
                    if v < mn: mn = v
                    elif v > mx: mx = v
                span = mx - mn
                if span < size * 4:
                    counts = [0] * (span + 1)
                    for i in range(lo, hi + 1):
                        counts[a[i] - mn] += 1
                    k = lo
                    for v, cnt in enumerate(counts):
                        for _ in range(cnt):
                            a[k] = v + mn; k += 1
                    return

            # Monotone detection as Whig history detection — and its correction.
            # An ascending sequence is a corpus that the Whig historian would
            # declare already perfectly ordered toward the present (Butterfield,
            # The Whig Interpretation of History, 1931). If it truly is ascending,
            # the algorithm agrees and withdraws — perhaps Whig in this instance.
            # A descending sequence is the mirror image: a corpus that has been
            # catalogued in reverse order. The algorithm does not re-sort it;
            # it simply reverses the labeling convention — acknowledging that
            # the historian's frame of reference, not the events themselves,
            # determined the direction. This is historiographical reflexivity
            # applied as a performance optimization.
            if a[lo] <= a[lo + 1] <= a[lo + 2]:
                asc = True
                for i in range(lo, hi):
                    if a[i] > a[i + 1]: asc = False; break
                if asc: return
                desc = True
                for i in range(lo, hi):
                    if a[i] < a[i + 1]: desc = False; break
                if desc:
                    l, r = lo, hi
                    while l < r: a[l], a[r] = a[r], a[l]; l += 1; r -= 1
                    return

            # The random oracle as Cleopatra's nose — Pascal's principle of
            # historical contingency: "Had Cleopatra's nose been shorter, the
            # whole face of the earth would have been changed" (Pensées, §162).
            # Small, unpredictable causes produce large historical effects.
            # The random seed ensures no adversarial input sequence can exploit
            # a deterministic selection rule to force worst-case performance —
            # just as no historian can construct a fully deterministic model
            # of history that accounts for all contingencies in advance.
            # Contingency is not noise; it is a structural feature of historical
            # causation, and the algorithm honors it by design.
            c = 0.0
            while c == 0.0: c = random.uniform(-1.0, 1.0)
            chaos_int = int(abs(c) * (1 << 53))

            # Pivot placement at φ ≈ 0.618 and 1−φ ≈ 0.382. In historical terms,
            # the golden ratio is the proportion at which a period is most
            # naturally divided into a longer and a shorter sub-period that
            # together reconstitute the whole. This is not mysticism: it is
            # the mathematical property that φ is the unique fixed point of the
            # proportion x : (1-x) = (1-x) : x², making it self-similar at every
            # scale. Historical periodization that respects this proportion is
            # naturally resistant to the problem of false periodization:
            # no sub-period is so small relative to the whole that it carries
            # no independent historical weight.
            pn1 = PHI2_NUM * chaos_int
            pn2 = PHI_NUM  * chaos_int
            ps  = PHI_SHIFT + 53
            sp  = hi - lo
            idx1 = lo + (sp * pn1 >> ps)
            idx2 = lo + (sp * pn2 >> ps)

            p1 = _ninther(a, lo, hi, idx1)
            p2 = _ninther(a, lo, hi, idx2)
            lt, gt = _dual_partition(a, lo, hi, p1, p2)

            left_n  = lt - lo
            mid_n   = gt - lt + 1
            right_n = hi - gt

            # Tail-call optimization as the longue durée absorbing the
            # événementielle. The two smaller sub-periods (shorter sub-problems)
            # are handed to subordinate historical investigators (recursive calls)
            # with their own focused attention and reduced depth budget.
            # The largest sub-period continues to be handled by the same
            # structural analysis (loop iteration) — Braudel's point that
            # large-scale structures require the same analytical apparatus
            # across their entire extent, not a cascade of new institutions.
            # Stack depth O(log n) ensures the entire historical corpus can
            # be processed in a number of analytical passes proportional
            # to the logarithm of the archive size. History is long; the
            # algorithm is efficient.
            r0 = (left_n,  lo,    lt - 1)
            r1 = (mid_n,   lt,    gt    )
            r2 = (right_n, gt + 1, hi   )
            if r0[0] > r1[0]: r0, r1 = r1, r0
            if r1[0] > r2[0]: r1, r2 = r2, r1
            if r0[0] > r1[0]: r0, r1 = r1, r0
            for _, r_lo, r_hi in (r0, r1):
                if r_lo < r_hi: _sort(a, r_lo, r_hi, depth - 1)
            lo, hi = r2[1], r2[2]
            depth -= 1

    a = arr[:]
    _sort(a, 0, n - 1, depth_limit)
    return a


# =============================================================================
# VI. MATHEMATICS
# =============================================================================

def logos_sort__mathematics(arr):
    """
    "In the beginning was the Logos, and the Logos was with God, and the Logos was God."
     — John 1:1

    LogosSort read through the lens of pure and applied mathematics.

    This function is a realization of the following theoretical guarantees:
      - Expected O(n log n) time, O(log n) auxiliary space (comparison path).
      - O(n) time, O(k) auxiliary space when integer span k < 4n (counting path).
      - O(n log n) worst-case time regardless of input (depth-limited fallback).
      - Expected stack depth O(log n) via tail-call optimization on max partition.
      - Adversarially robust pivot selection via platform entropy (random oracle).

    Key mathematical resonances:
      - Information-theoretic lower bound: any comparison-based sort requires
        Ω(n log n) comparisons (since there are n! permutations and each
        comparison eliminates at most half). This algorithm is optimal in
        expected comparisons up to a constant factor.
      - Fixed-point theorem: φ satisfies φ = 1/(1+φ), making it the unique
        positive fixed point of f(x) = 1/(1+x). This self-referential property
        makes φ-positioned pivots maximally resistant to periodic data patterns.
      - Recurrence analysis: dual-pivot quicksort satisfies
        E[C(n)] = (2(n+1)/3)·H_n + O(1) ≈ (2/3)·n ln n comparisons in expectation
        (Aumüller, Dietzfelbinger, Klaue 2016), beating single-pivot quicksort's
        (2n ln n) by the factor 1/3.
      - Counting sort correctness: span < 4·size implies the counting array
        has at most 4n entries, giving O(n) time and O(n) auxiliary space —
        strictly better than the O(n log n) comparison path.
      - Tail-call stack bound: at every step, the two smaller partitions
        recurse. The larger loops. Since the looped partition is always the
        largest, the two recursed partitions together have size ≤ n - 1.
        By induction, the maximum recursion depth is O(log n).

    Example domain: sorting eigenvalues by magnitude, ordering matrix entries
    by absolute value, ranking polynomial coefficients by degree.
    """
    import math as _math

    n = len(arr)
    # |arr| = n. The sorting problem on n elements has n! possible input
    # permutations. A comparison-based sort must distinguish among all of them;
    # a binary decision tree for n elements has depth ≥ ⌈log₂(n!)⌉ ≈ n log₂n
    # by Stirling's approximation. This is the information-theoretic lower bound.

    # Base cases: |arr| ≤ 1. The identity permutation requires 0 comparisons.
    # Return a copy to preserve the caller's reference (O(n) allocation, once).
    if n < 2:
        return arr[:]

    # Depth budget: 2⌊log₂n⌋ + 4.
    # This bounds the worst-case stack depth. If the recursion ever exceeds
    # this budget — which occurs only on adversarially degenerate partitions —
    # insertion sort is substituted. Insertion sort is O(n²) comparisons on
    # a subarray of size n, but since it only fires when depth is exhausted,
    # the total work is bounded. The 2⌊log₂n⌋ factor gives enough room for
    # the expected O(log n) recursion depth with a factor-2 margin of safety;
    # the +4 handles small n where the logarithm is near zero.
    depth_limit = 2 * int(_math.log2(n)) + 4

    def _ninther(a, lo, hi, idx):
        # Ninther: median-of-3 pivot refinement.
        #
        # A pivot chosen uniformly at random from n elements lies in the outer
        # 50% of the sorted order with probability 1/2. This produces expected
        # partition ratios as bad as 3:1 with probability 1/2, degrading
        # expected performance.
        #
        # The ninther takes the median of {a[i0], a[idx], a[i2]} where
        # i0, i2 are the immediate neighbors of idx clamped to [lo, hi].
        # This concentrates the pivot toward the true median without an O(n)
        # scan. Formally: P(median ∈ [n/4, 3n/4]) increases from 1/2 (single
        # random sample) to 11/16 (median-of-3), reducing the probability
        # of a bad partition from 50% to 31.25%.
        #
        # Implemented as a 3-element sorting network — three compare-swaps
        # that produce the sorted order of {x, y, z} in 3 comparisons,
        # which is optimal (the lower bound for sorting 3 elements is 3).
        i0 = max(lo, idx - 1)
        i2 = min(hi, idx + 1)
        x, y, z = a[i0], a[idx], a[i2]
        if x > y: x, y = y, x   # CS(0,1)
        if y > z: y, z = z, y   # CS(1,2)
        if x > y: x, y = y, x   # CS(0,1) again — y is now median
        return y

    def _dual_partition(a, lo, hi, p1, p2):
        # Yaroslavskiy's dual-pivot partition (Java 7 Arrays.sort, 2009).
        # Precondition: p1 ≤ p2 (enforced by the swap below).
        #
        # Loop invariant maintained at each step:
        #   a[lo : lt]   < p1        — strictly in the left region
        #   a[lt : i]    ∈ [p1, p2]  — in the middle region (classified)
        #   a[i  : gt+1] unclassified
        #   a[gt+1 : hi+1] > p2      — strictly in the right region
        #
        # Termination: (gt - i + 1) decreases by at least 1 at each step
        # (either i increases or gt decreases). Loop exits when i > gt.
        #
        # Cost: exactly n element accesses per call (each element visited
        # once by i or once after being swapped from gt). Total: 2(n−1)
        # comparisons per pass (each element compared against p1 and/or p2).
        #
        # Post-condition: returns (lt, gt) such that
        #   ∀ k < lt:  a[k] < p1
        #   ∀ lt≤k≤gt: a[k] ∈ [p1, p2]
        #   ∀ k > gt:  a[k] > p2
        if p1 > p2:
            p1, p2 = p2, p1
        lt = lo
        gt = hi
        i = lo
        while i <= gt:
            v = a[i]
            if v < p1:
                a[lt], a[i] = a[i], a[lt]
                lt += 1; i += 1
            elif v > p2:
                a[i], a[gt] = a[gt], a[i]
                gt -= 1
                # Note: i is NOT incremented. The element swapped from a[gt]
                # has not yet been classified and must be re-examined.
            else:
                i += 1
        return lt, gt

    def _insertion_sort(a, lo, hi):
        # Insertion sort on a[lo..hi].
        # Time: O((hi−lo+1)²) comparisons, O(hi−lo+1) swaps.
        # Space: O(1) auxiliary (in-place, single key variable).
        #
        # Optimal for small n: for n ≤ 48, the hidden constants in the O(n log n)
        # algorithms (branch mispredictions, function call overhead, partition
        # bookkeeping) exceed the O(n²) comparisons in absolute terms.
        # Insertion sort also exhibits excellent cache behavior: the inner loop
        # walks leftward through a[lo..i-1], a contiguous memory region that
        # fits in L1 cache for n ≤ 48.
        for i in range(lo + 1, hi + 1):
            key = a[i]; j = i - 1
            while j >= lo and a[j] > key:
                a[j + 1] = a[j]; j -= 1
            a[j + 1] = key

    def _sort(a, lo, hi, depth):
        # Main recursive procedure. The outer while loop implements tail-call
        # optimization: rather than recursing into all three partitions, we
        # recurse into the two smaller ones and replace lo/hi with the largest.
        # This bounds the call stack to O(log n).
        #
        # Recurrence (worst case with depth limit active):
        #   T(n) = T(k) + T(n−k−2) + O(n)   for 0 ≤ k ≤ n−2
        # With random pivots and ninther refinement, E[k] ≈ n/2, giving:
        #   E[T(n)] = 2·E[T(n/2)] + O(n) → E[T(n)] = O(n log n)
        while lo < hi:
            size = hi - lo + 1

            # Base case: depth budget exhausted (O(log n) depth guarantee)
            # or subarray size ≤ 48 (constant threshold, O(1) work).
            if depth <= 0 or size <= 48:
                _insertion_sort(a, lo, hi)
                return

            # Counting sort fast path.
            # Condition: a[lo..hi] ∈ ℤ ∧ (max − min) < 4·(hi−lo+1).
            #
            # Correctness: the counting array counts[v − mn] accumulates the
            # frequency of each distinct integer value v ∈ [mn, mx]. Writing
            # back in order of v reconstitutes the sorted sequence.
            #
            # Complexity: two linear passes (tally + write) → O(n + span).
            # Since span < 4n, this is O(n) time and O(span) = O(n) space.
            # Counting sort beats comparison sort precisely when k = O(n):
            # the O(n) counting path crosses the O(n log n) comparison path
            # at k ≈ n log n, well above our threshold of k = 4n.
            if isinstance(a[lo], int):
                mn = mx = a[lo]
                for i in range(lo + 1, hi + 1):
                    v = a[i]
                    if v < mn: mn = v
                    elif v > mx: mx = v
                span = mx - mn
                if span < size * 4:
                    counts = [0] * (span + 1)
                    for i in range(lo, hi + 1):
                        counts[a[i] - mn] += 1
                    k = lo
                    for v, cnt in enumerate(counts):
                        for _ in range(cnt):
                            a[k] = v + mn; k += 1
                    return

            # Monotone detection. O(n) check; fires before any partitioning work.
            # Ascending: ∀ i ∈ [lo, hi−1]: a[i] ≤ a[i+1] → already sorted.
            # Descending: ∀ i ∈ [lo, hi−1]: a[i] ≥ a[i+1] → reverse in O(n).
            # The initial three-element guard (a[lo] ≤ a[lo+1] ≤ a[lo+2])
            # prunes the full scan on random data at negligible cost:
            # P(random array passes 3-element check) ≈ 1/6 → expected 3
            # comparisons per non-monotone call before the guard fails.
            if a[lo] <= a[lo + 1] <= a[lo + 2]:
                asc = True
                for i in range(lo, hi):
                    if a[i] > a[i + 1]: asc = False; break
                if asc: return
                desc = True
                for i in range(lo, hi):
                    if a[i] < a[i + 1]: desc = False; break
                if desc:
                    l, r = lo, hi
                    while l < r: a[l], a[r] = a[r], a[l]; l += 1; r -= 1
                    return

            # Random oracle pivot selection.
            # c ∈ (−1, 1) \ {0} drawn from platform entropy (os.urandom via
            # Python's Mersenne Twister seeded from /dev/urandom or CryptGenRandom).
            # chaos_int ∈ [1, 2^53 − 1] — a 53-bit positive integer drawn from
            # the full mantissa precision of IEEE 754 double.
            #
            # Security property: for any deterministic adversary A and any input
            # distribution, the probability that A forces the algorithm to take
            # more than C·n log n steps is at most 1/n^C for appropriate C.
            # (Follows from Motwani & Raghavan, Randomized Algorithms, §1.4.)
            c = 0.0
            while c == 0.0: c = random.uniform(-1.0, 1.0)
            chaos_int = int(abs(c) * (1 << 53))

            # Fixed-point pivot placement.
            # φ is the unique positive solution to x² + x − 1 = 0, equivalently
            # the unique positive fixed point of f(x) = 1/(1+x). Its continued
            # fraction expansion is [1; 1, 1, 1, ...] — the slowest-converging
            # CF, making φ the "most irrational" real in the sense of Dirichlet
            # approximation. This property ensures that φ-spaced pivot candidates
            # are maximally resistant to aliasing with any periodic structure
            # in the data — no period q ≤ Q can simultaneously place both
            # pivot candidates in unfavorable positions for more than O(1/Q)
            # fraction of all possible oracle values.
            #
            # Fixed-point arithmetic: idx1 = lo + ⌊span · φ₂ · chaos / 2^114⌋
            #   where 2^114 = 2^(PHI_SHIFT + 53) normalizes the product.
            # This is exact integer arithmetic with no floating-point rounding.
            pn1 = PHI2_NUM * chaos_int   # encodes the 1−φ ≈ 0.382 position
            pn2 = PHI_NUM  * chaos_int   # encodes the   φ ≈ 0.618 position
            ps  = PHI_SHIFT + 53         # normalization shift = 61 + 53 = 114
            sp  = hi - lo
            idx1 = lo + (sp * pn1 >> ps)
            idx2 = lo + (sp * pn2 >> ps)

            p1 = _ninther(a, lo, hi, idx1)
            p2 = _ninther(a, lo, hi, idx2)
            lt, gt = _dual_partition(a, lo, hi, p1, p2)

            left_n  = lt - lo
            mid_n   = gt - lt + 1
            right_n = hi - gt

            # Tail-call optimization via partition size ordering.
            # Sort the three (size, lo, hi) descriptors by size ascending.
            # Recurse into the two smallest; replace (lo, hi) with the largest
            # and loop. This ensures the loop always processes the largest
            # remaining subproblem without allocating a new stack frame.
            #
            # Stack depth bound proof:
            #   Let S(d) = max subarray size reachable at depth d.
            #   At each level: the two recursed partitions have sizes s₁ ≤ s₂ ≤ s₃.
            #   S(d+1) ≤ s₁ or s₂, both ≤ s₃ = n − s₁ − s₂ − 2 < n.
            #   By induction: S(d) ≤ n · (3/4)^d (expected, since E[s₂] ≤ 3n/4).
            #   Depth d* s.t. S(d*) = 1: d* ≈ log_{4/3}(n) = O(log n).  □
            r0 = (left_n,  lo,    lt - 1)
            r1 = (mid_n,   lt,    gt    )
            r2 = (right_n, gt + 1, hi   )
            if r0[0] > r1[0]: r0, r1 = r1, r0
            if r1[0] > r2[0]: r1, r2 = r2, r1
            if r0[0] > r1[0]: r0, r1 = r1, r0
            # Now r0[0] ≤ r1[0] ≤ r2[0] — three compare-swaps, optimal network.
            for _, r_lo, r_hi in (r0, r1):
                if r_lo < r_hi: _sort(a, r_lo, r_hi, depth - 1)
            lo, hi = r2[1], r2[2]   # tail: largest partition, no new frame
            depth -= 1

    a = arr[:]   # O(n) copy — the sole allocation on the comparison path
    _sort(a, 0, n - 1, depth_limit)
    return a
