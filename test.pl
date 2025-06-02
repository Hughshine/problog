
0.974337::time(1).
0.864272::rand_number(1, 3).
0.978481::key_number(1, 12).
0.926085::share(4, 9).
0.900964::share(9, 3).
0.801154::share(3, 7).
0.933842::share(7, 6).
0.965289::share(6, 9).
0.878296::share(9, 5).
0.874126::share(5, 8).
0.847438::share(8, 6).
0.842164::share(6, 49).
0.884553::share(4, 8).
0.878943::rand(11).
0.840113::rec_rand_var(11, 1, 1).
0.978773::rec_all_inc(11, 1, 1).
store_assign(1, 11).
0.852357::rand(13).
0.8854::rec_rand_var(13, 1, 2).
0.953706::rec_all_inc(13, 1, 2).
store_assign(2, 13).
0.986966::key_sensitive(15).
0.966766::rec_rand_var(15, 1, 0).
0.955026::rec_all_inc(15, 1, 4).
store_assign(3, 15).
0.882515::key_sensitive(17).
0.91494::rec_rand_var(17, 1, 0).
0.855669::rec_all_inc(17, 1, 8).
store_assign(4, 17).
load_assign(19, 4).
0.961071::trunc_assign(20, 19).
0.946778::zext_assign(21, 20).
load_assign(22, 1).
0.923015::trunc_assign(23, 22).
0.984827::zext_assign(24, 23).
xor_assign_left(25, 21).
xor_assign_right(25, 24).
0.813591::icmp_assign(26, 25).
0.800635::zext_assign(27, 26).
store_assign(9, 27).
load_assign(29, 3).
0.804159::trunc_assign(30, 29).
0.982937::zext_assign(31, 30).
load_assign(32, 1).
0.938856::trunc_assign(33, 32).
0.982752::zext_assign(34, 33).
xor_assign_left(35, 31).
xor_assign_right(35, 34).
0.879102::icmp_assign(36, 35).
0.969384::zext_assign(37, 36).
store_assign(7, 37).
load_assign(39, 7).
0.974001::trunc_assign(40, 39).
0.965983::zext_assign(41, 40).
0.912421::binary_constant(42, 41).
0.935906::icmp_assign(43, 42).
0.941808::zext_assign(44, 43).
store_assign(6, 44).
load_assign(46, 9).
0.918183::trunc_assign(47, 46).
0.936756::zext_assign(48, 47).
0.986291::binary_constant(49, 48).
0.884557::icmp_assign(50, 49).
0.85187::zext_assign(51, 50).
store_assign(5, 51).
load_assign(53, 5).
0.837578::trunc_assign(54, 53).
0.860262::zext_assign(55, 54).
0.954409::binary_constant(56, 55).
0.960862::icmp_assign(57, 56).
0.945918::zext_assign(58, 57).
store_assign(8, 58).
load_assign(60, 6).
0.964153::trunc_assign(61, 60).
0.895145::zext_assign(62, 61).
0.968889::binary_constant(63, 62).
0.914451::icmp_assign(64, 63).
0.874724::zext_assign(65, 64).
store_assign(10, 65).
load_assign(67, 8).
0.864331::trunc_assign(68, 67).
0.857881::zext_assign(69, 68).
load_assign(70, 10).
0.918156::trunc_assign(71, 70).
0.934491::zext_assign(72, 71).
0.903381::assign(73, 69).
0.830985::assign(73, 72).
0.814976::icmp_assign(74, 73).

check_same(FROM1, FROM2) :- (xor_assign_left(TO, FROM1), xor_assign_right(TO, FROM2), time(TIMES), ((rand(FROM1), bv_diff_rec(FROM1, FROM2, TIMES, INT_RES0), (INT_RES0 = 0)), (rand(FROM2), bv_diff_rec(FROM2, FROM1, TIMES, INT_RES1), (INT_RES1 = 0)))).
diff_label(FROM1, FROM2) :- (xor_assign_left(TO, FROM1), xor_assign_right(TO, FROM2), rand(FROM1)).
diff_label(FROM2, FROM1) :- (xor_assign_left(TO, FROM1), xor_assign_right(TO, FROM2), rand(FROM2)).
0.994382::hd_sensitive(TO, FROM) :- (share(TO, FROM), equal_assign(from_e, FROM), equal_assign(to_e, TO), xor_assign_left(to_e, FROM1), xor_assign_right(to_e, from_e), key_sensitive(FROM1)).
0.994382::hd_sensitive(TO, FROM) :- (share(TO, FROM), equal_assign(from_e, FROM), equal_assign(to_e, TO), xor_assign_left(to_e, from_e), xor_assign_right(to_e, FROM1), key_sensitive(FROM1)).
0.849833::hd_sensitive(TO, FROM1) :- (xor_assign_left(TO, FROM1), xor_assign_right(TO, FROM2), share(TO, FROM1), key_sensitive(FROM2)).
0.849833::hd_sensitive(TO, FROM2) :- (xor_assign_left(TO, FROM1), xor_assign_right(TO, FROM2), share(TO, FROM2), key_sensitive(FROM1)).
0.912716::intersect_label(FROM1, FROM2) :- (xor_assign_left(TO, FROM1), xor_assign_right(TO, FROM2), key_ind(FROM1), key_ind(FROM2)).
key_ind(TO) :- ((equal_assign(FROM1, TO); TO = FROM1), key_ind(FROM1)).
key_ind(TO) :- ((equal_assign(TO, FROM1); TO = FROM1), key_ind(FROM1)).
0.95548::key_ind(TO) :- (binary_constant(TO, FROM1), key_ind(FROM1)).
0.814331::key_ind(TO) :- (load_assign(TO, FROM1), key_ind(FROM1)).
0.843516::key_ind(TO) :- (store_assign(TO, FROM1), key_ind(FROM1)).
key_ind(TO) :- (xor_assign_left(TO, FROM1), xor_assign_right(TO, FROM2), key_ind(FROM1), key_ind(FROM2), time(TIMES), bv_intersect_rec(FROM1, FROM2, TIMES, INT_RES0), (INT_RES0 = 0)).
key_ind(TO) :- (xor_assign_left(TO, FROM1), xor_assign_right(TO, FROM2), time(TIMES), (rand(FROM1); rand(FROM2)), bv_same_rec(FROM1, FROM2, TIMES, INT_RES0), (INT_RES0 = 0)).
key_sensitive(TO) :- ((equal_assign(FROM1, TO); TO = FROM1), key_sensitive(FROM1)).
key_sensitive(TO) :- ((equal_assign(TO, FROM1); TO = FROM1), key_sensitive(FROM1)).
0.855186::key_sensitive(TO) :- (binary_constant(TO, FROM1), key_sensitive(FROM1)).
0.81677::key_sensitive(TO) :- (load_assign(TO, FROM1), key_sensitive(FROM1)).
0.833725::key_sensitive(TO) :- (store_assign(TO, FROM1), key_sensitive(FROM1)).
key_sensitive(TO) :- (xor_assign_left(TO, FROM1), xor_assign_right(TO, FROM2), key_ind(FROM1), key_ind(FROM2), time(TIMES), bv_intersect_rec(FROM1, FROM2, TIMES, INT_RES0), \+((INT_RES0 = 0))).
0.954252::key_sensitive(TO) :- (xor_assign_left(TO, FROM1), xor_assign_right(TO, FROM2), key_sensitive(FROM1), key_sensitive(FROM2)).
key_sensitive(TO) :- (xor_assign_left(TO, FROM1), xor_assign_right(TO, FROM2), time(TIMES), (rand(FROM1); rand(FROM2)), bv_same_rec(FROM1, FROM2, TIMES, INT_RES0), \+((INT_RES0 = 0))).
rand(TO) :- ((equal_assign(FROM1, TO); TO = FROM1), rand(FROM1)).
rand(TO) :- ((equal_assign(TO, FROM1); TO = FROM1), rand(FROM1)).
0.896764::rand(TO) :- (binary_constant(TO, FROM1), rand(FROM1)).
0.84821::rand(TO) :- (load_assign(TO, FROM1), rand(FROM1)).
0.939405::rand(TO) :- (store_assign(TO, FROM1), rand(FROM1)).
rand(TO) :- (xor_assign_left(TO, FROM1), xor_assign_right(TO, FROM2), time(TIMES), ((rand(FROM1), bv_diff_rec(FROM1, FROM2, TIMES, INT_RES0), \+((INT_RES0 = 0))); (rand(FROM2), bv_diff_rec(FROM2, FROM1, TIMES, INT_RES1), \+((INT_RES1 = 0))))).
0.982548::tdep(TO, FROM) :- assign(TO, FROM).
0.822016::tdep(TO, PREV) :- (assign(TO, FROM), tdep(FROM, PREV)).
0.911705::assign(TO, FROM) :- load_assign(TO, FROM).
0.993681::assign(TO, FROM) :- store_assign(TO, FROM).
0.992146::assign(TO, FROM2) :- (assign(TO, FROM1), assign(FROM1, FROM2)).
0.975596::equal_assign(FROM1, TO) :- (equal_assign(FROM1, FROM2), equal_assign(FROM2, TO)).
0.824633::equal_assign(TO, FROM1) :- assign(TO, FROM1).
0.816296::equal_assign(TO, FROM1) :- binary_constant(TO, FROM1).
0.981936::load_assign(TO, FROM1) :- icmp_assign(TO, FROM1).
0.826274::load_assign(TO, FROM1) :- trunc_assign(TO, FROM1).
0.948581::load_assign(TO, FROM1) :- zext_assign(TO, FROM1).
0.842829::share(FROM2, FROM1) :- share(FROM1, FROM2).

query(key_sensitive(_)).

query(key_ind(_)).
