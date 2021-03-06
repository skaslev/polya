(*
Theory: isabelle_problems.thy
Author: Jeremy avigad

Sample problems, for comparison with the Polya inequality prover.
*)

theory isabelle_problems

imports Complex_Main

begin

(* sledgehammer and auto fail on this *)
lemma "(0::real) < u ==> u < v ==> v < 1 ==> 2 <= x ==> x <= y ==> 2 * u * v^2 < v * y^2"
  apply (simp add: field_simps eval_nat_numeral)
by (rule mult_strict_mono, auto)

(* even this is nontrivial for sledgehammer *)
lemma one_plus_square_gt_0: "(0 :: real) < 1 + y^2"
by (metis add.commute less_add_one linorder_neqE_linordered_idom pos_add_strict 
  power2_less_0 zero_less_one)

(* but sledgehammer eventually finds an easy solution using z3 *)
lemma "(0 :: real) < 1 + y^2"
by (smt power2_less_0)

(* sledgehammer and auto fail on this *)
lemma "(1::real) < x ==> (1 + y^2) * x > (1 + y^2)"
  apply (subst mult.right_neutral [of "1 + y^2", symmetric])
  apply (rule mult_le_less_imp_less, auto)
by (rule one_plus_square_gt_0) 

(* sledgehammer and auto fail on this *)
lemma "(0::real) < x ==> x < 1 ==> 1 / (1 - x) > 1 / (1 - x^2)"
  apply (auto simp add: field_simps eval_nat_numeral)
  apply (rule mult_imp_div_pos_less)
  apply (auto simp add: field_simps)
  apply (subst mult.right_neutral [of 1, symmetric])
by (rule mult_strict_mono, auto)

(* sledgehammer and auto fail on this *)
lemma "(0::real) < u ==> u < v ==> 0 < z ==> z + 1 < w ==> (u + v + w)^3 < (u + v + w + 1)^5"
  apply (rule order_less_trans)
  apply (rule power_strict_mono)
  prefer 4
  apply (rule power_strict_increasing)
by auto

(* sledgehammer and auto fail on this *)
lemma "(0::real) < u ==> u < v ==> 0 < z ==> z + 1 < w ==> (u + v + w)^33 < (u + v + w + 1)^55"
  apply (rule order_less_trans)
  apply (rule power_strict_mono)
  prefer 4
  apply (rule power_strict_increasing)
by auto

(* sledgehammer and auto fail on this *)
lemma "(0::real) < u ==> u < (v^2 + 23)^3 ==> 0 < z ==> z + 1 < w ==> 
    (u + (v^2 + 23)^3 + w)^3 < (u + (v^2 + 23)^3 + w + 1)^5"
  apply (rule order_less_trans)
  apply (rule power_strict_mono)
  prefer 4
  apply (rule power_strict_increasing)
by auto

(* sledgehammer gets this easily *)
lemma "(ALL x y. x <= y --> f x <= f y) ==> (u::real) < v ==> (x::real) <= y ==> 
    u + f x < v + f y"
by (metis add_less_le_mono)

(* sledgehammer finds a solution with Z3 *)
lemma "(ALL x y. x <= y --> f x <= f y) ==> (u::real) < v ==> 1 < v ==> (x::real) <= y ==> 
    f x + u < v^2 + f y"
by (smt add_mono_thms_linordered_field(5) numeral_One numeral_le_iff power_increasing_iff 
power_one_right semiring_norm(69))

(* but fails here *)
lemma "(ALL x y. x <= y --> f x <= f y) ==> (u::real) < v ==> 1 < w ==> 2 < s ==> 
    (w + s) / 3 < v ==> (x::real) <= y ==> f x + u < v^2 + f y"
  apply (drule_tac x = x in spec)
  apply (drule_tac x = y in spec)
  apply (erule impE, assumption)
  apply (subst add.commute)
  apply (rule add_less_le_mono, auto simp add: eval_nat_numeral)
  apply (subst mult.right_neutral [of u, symmetric])
by (rule mult_strict_mono, auto)

(* sledgehammer finds a solution with Z3 *)
lemma "(ALL x y. x <= y --> f x <= f y) ==> (u::real) < v ==> 1 < v ==> (x::real) <= y ==> 
    f x + u < (1 + v)^10 + f y"
sorry  (* with Isabelle 2014, no longer works *)
(* by (smt power_one_right power_strict_increasing_iff) *)

(* sledgehammer gets this with resolution *)
lemma "(ALL x. f x <= 1) ==> (0::real) < w ==> u < v ==> u + w * f x < v + w"
by (metis add_less_le_mono monoid_mult_class.mult.right_neutral real_mult_le_cancel_iff2)

(* but it doesn't get this *)
lemma "(ALL x. f x <= 2) ==> (0::real) < w ==> u < v ==> u + w * (f x - 1) < v + w"
  apply (erule add_less_le_mono)
  apply (subst (2) mult.right_neutral [of w, symmetric])
  by (rule mult_left_mono, auto)

(* problems with built-in functions *)
lemma "(z :: real) > exp x \<Longrightarrow> w > exp y \<Longrightarrow> z^3 * w^2 > exp (3 * x + 2 * y)"
apply (subgoal_tac "exp (3 * x + 2 * y) = (exp x)^3 * (exp y)^2")
prefer 2
apply (simp add: exp_add exp_real_of_nat_mult [symmetric])
apply (erule ssubst)
apply (rule mult_strict_mono)
apply (rule power_strict_mono, auto)
apply (rule power_strict_mono, auto)
apply (rule le_less_trans)
prefer 2
apply assumption
by auto

(* sledgehammer gets this one *)
lemma "(u::real) > 0 \<Longrightarrow> v > 0 \<Longrightarrow> x > 0 \<Longrightarrow> ln x > 2 * u + v \<Longrightarrow> x > 1"
by (metis add_less_cancel_left add_strict_mono comm_monoid_add_class.add.right_neutral linorder_neqE_linordered_idom ln_less_zero_iff ln_one monoid_add_class.add.left_neutral mult.commute mult_2_right order_less_irrefl pos_add_strict)

lemma "(x :: real) < y \<Longrightarrow> u \<le> v \<Longrightarrow> u + min (x + 2 * u) (y + 2 * v) \<le> x + 3 * v"
by auto

lemma "y > (0::real) \<Longrightarrow> abs (3 * x + 2 * y + 5) < 4 * abs(x) + 3 * y + 6"
by (auto split: abs_split)

lemma "(u::real) > 0 \<Longrightarrow> v > 0 \<Longrightarrow> root 3 (u^9 * v^4) > u^3 * v"
sorry

lemma "exp(max (abs (x::real)) y) \<ge> 1"
by auto

lemma "y > (0::real) \<Longrightarrow> ln (1 + abs(x) + y) > 0"
by auto

lemma "y > 0 \<Longrightarrow> ln (1 + abs(x) + y^4) > 0"
apply (subgoal_tac "1 + abs(x) + y^4 > 1")
using ln_gt_zero apply blast
by (metis abs_power2 is_num_normalize(1) less_add_same_cancel1 pos_add_strict power_zero_numeral zero_less_abs_iff zero_less_power)

(* sledgehammer finds a solution using resolution *)
lemma "(0::real) < x ==> x < y ==> u < v ==>
    2 * u + exp (1 + x + x^4) <= 2 * v + exp (1 + y + y^4)"
by (metis add_less_cancel_left add_mono_thms_linordered_field(5) exp_less_cancel_iff 
    less_eq_real_def mult_2 power_strict_mono zero_less_numeral)

(* sledgehammer finds a solution using Z3 *)
lemma "(0::real) < x ==> x < y ==> u < v ==>
    2 * u + exp (1 + x + x^4) <= 2 * v + exp (1 + y + y^4)"
by (smt exp_le_cancel_iff power_less_imp_less_base)

(* sledgehammer and auto fail *)
lemma "(0::real) < x ==> 3 < y ==> (u::real) < v ==>
    2 * u + exp 10 <= 2 * v + exp (1 + y^2)"
thm add_mono [of u v]
  apply (rule add_mono)
  apply (auto simp add: eval_nat_numeral)
  apply (subgoal_tac "9 = 3 * 3")
  apply (erule ssubst)
by (rule mult_mono, auto)

(* Z3 does fine here *)
lemma "(ALL (x::real) y. f(x + y) = f(x) + f(y)) ==> f(a + b) > (2::real) ==> f(c + d) > 2 ==>
    f(a + b + c + d) > 4"
by smt

(* but sledgehammer fails here *)
lemma "(ALL (x::real) y. f (x + y) = f x * f y) ==> f a > (2::real) ==> f b > 2 ==>
    f(a + b) > 4"
  apply simp
  apply (subgoal_tac "4 = 2 * 2")
  apply (erule ssubst)
  apply (rule mult_strict_mono)
by auto

(* and all the more so here *)
lemma "(ALL (x::real) y. f(x + y) = f(x) * f(y)) ==> f(a + b) > (2::real) ==> f(c + d) > 2 ==>
    f(a + b + c + d) > 4"
  apply (drule_tac x = "a + b" in spec)
  apply (drule_tac x = "c + d" in spec)
  apply (simp add: add.assoc)
  apply (subgoal_tac "4 = 2 * 2")
  apply (erule ssubst) back
  apply (rule mult_strict_mono)
by auto 

(* sledgehammer fails here *)
lemma "(0::real) <= n ==> n < (K / 2) * x ==> 0 < C ==> 0 < eps ==> eps < 1 ==> 
    (1 + eps / (3 * (C + 3))) * n < K * x"
  apply (subgoal_tac "K * x = 2 * ((K / 2) * x)")
  apply (erule ssubst)
by (rule mult_le_less_imp_less, auto simp add: field_simps)

(* sledgehammer fails here *)
lemma "(0::real) < x ==> x < y ==> (1 + x^2) / (2 + y)^17 < (1 + y^2) / (2 + x)^10"
  apply (simp add: divide_simps)
  apply (rule mult_strict_mono, auto)
  apply (rule power_strict_mono, auto)
  apply (rule order_le_less_trans)
  apply (rule power_mono [of "2 + x" "2 + y"], auto)
by (rule one_plus_square_gt_0) 

(* sledgehammer fails here *)
lemma "(0::real) < x ==> x < y ==> (1 + x^2) / (2 + exp y) < (1 + y^2) / (2 + exp x)"
  apply (subgoal_tac "exp x > 0")
  apply (subgoal_tac "exp y > 0")
  apply (auto simp add: divide_simps simp del: exp_gt_zero)
  apply (rule mult_strict_mono)
  apply (auto simp del: exp_gt_zero)
  apply (rule power_strict_mono, auto)
by (rule one_plus_square_gt_0) 


(* from the Isabelle mailing list - Sledgehammer gets it *)
lemma "(0::real) < x ==> 0 < y ==> y < 1 ==> x + y > x * y"
by (metis add_strict_mono monoid_add_class.add.right_neutral monoid_mult_class.mult.left_neutral 
  mult.commute real_mult_less_iff1)

(* Sledgehammer fails *)
lemma "(0::real) < x ==> 0 < y ==> y < 1 ==> x + y^150 > x * y^150"
  apply (rule order_le_less_trans)
  apply (rule mult_right_le_one_le, auto)
by (rule power_le_one, auto)

(* a slight variant *)
lemma "(0::real) < x ==> -1 < y ==> y < 0 ==> x + (y + 1)^150 > x * (y + 1)^150"
  apply (rule order_le_less_trans)
  apply (rule mult_right_le_one_le, auto)
by (rule power_le_one, auto)

(* a calculation taken from a formalization *)
lemma
  fixes m :: int and 
    f :: "int => real" and
    x a b :: real
  assumes 
    f_prop: "!!m. m > 0 ==> f m < a + (b - a) / m" and 
    "a < b" "x > a" and
    *: "m >= ceiling((b - a) / (x - a)) + 1"
  shows "f m < x"
proof -
  from * have **: "real m > ((b - a) / (x - a))"
    by (metis add.commute ceiling_real_of_int less_ceiling_eq less_linear not_le 
        pos_add_strict zero_less_one zle_add1_eq_le)
  have ***: "real m > 0"
    apply (rule order_less_trans [OF _ **])
    using `a < b` `x > a` by (simp add: field_simps)
  hence "m > 0" by simp
  hence "f m < a + (b - a) / m" by (intro f_prop)
  also have "... < a + (b - a) / ((b - a) / (x - a))"
    apply (rule add_strict_left_mono)
    apply (rule divide_strict_left_mono)
    apply (rule **)
    using assms *** by (auto simp add: field_simps)
  also with `a < b` have "... = x" 
    by (simp add: field_simps)
  finally show ?thesis .
qed

(* instead of integers, stick to reals *)
lemma
  fixes m :: real and 
    f ceil :: "real => real" and
    x a b :: real
  assumes 
    ceil_prop: "!!x. ceil x >= x" and
    f_prop: "!!m. m > 0 ==> 
      f (ceil m) < a + (b - a) / (ceil m)" and 
    "a < b" "x > a" and
    *: "m >= ((b - a) / (x - a)) + 1"
  shows "f (ceil m) < x"
proof -
  have "m > 0"
    apply (rule order_less_le_trans [OF _ *])
    using `a < b` `x > a` by (simp add: field_simps)
  hence "f (ceil m) < a + (b - a) / (ceil m)" by (intro f_prop)
  also have "... < a + (b - a) / ((b - a) / (x - a))"
    apply (rule add_strict_left_mono)
    apply (rule divide_strict_left_mono)
    apply (rule order_less_le_trans [OF _ ceil_prop])
    apply (rule order_less_le_trans [OF _ *])
    using `a < b` apply auto
    using `x > a` apply (simp add: field_simps)
    apply (erule mult_strict_right_mono)
    apply (rule order_less_le_trans [OF _ ceil_prop])
    by (rule `m > 0`)
  also with `a < b` have "... = x" 
    by (simp add: field_simps)
  finally show ?thesis .
qed

(* Another example taking from a proof that the set of continuity points of a function is 
   borel; see Billingsley, *Probability and Measure*, third edition, footnote on page 334. *)
lemma "i > (0::real) ==> abs(f y - f x) < 1 / (2 * (i + 1)) ==> 
    abs(f z - f y) < 1 / (2 * (i + 1)) ==> abs(f z - f x) < 1 / (i + 1)"
  apply (subgoal_tac "f z - f x = (f z - f y) + (f y - f x)")
  apply (erule ssubst)
  apply (rule order_le_less_trans)
  apply (rule abs_triangle_ineq)
  apply (rule order_less_le_trans)
  apply (erule (1) add_strict_mono)
by (auto simp add: field_simps)

end
  