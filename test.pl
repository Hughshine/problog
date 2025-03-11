% ============================================================
% ProbLog Alarm example
% ------------------------------------------------------------
% 0.01 chance of burglary
% 0.02 chance of earthquake
% Alarm probability depends on burglary/earthquake
% John/Mary call depending on Alarm
% ============================================================

% ─── Probabilistic Facts ────────────────────────────────────

0.01::burglary.
0.02::earthquake.

% If both burglary and earthquake happen:
0.95::alarm :- burglary, earthquake.
% If burglary but no earthquake:
0.94::alarm :- burglary, \+earthquake.
% If earthquake but no burglary:
0.29::alarm :- \+burglary, earthquake.
% If neither burglary nor earthquake:
0.001::alarm :- \+burglary, \+earthquake.

% JohnCalls and MaryCalls depend on Alarm:
0.90::johnCalls :- alarm.
0.05::johnCalls :- \+alarm.

0.70::maryCalls :- alarm.
0.01::maryCalls :- \+alarm.

% ─── Evidence ────────────────────────────────────────────────
% We’ve observed that both John and Mary called:
evidence(johnCalls, true).
evidence(maryCalls, true).

% ─── Queries ────────────────────────────────────────────────
% Ask for the posterior probabilities of burglary, earthquake, alarm:
query(burglary).
query(earthquake).
query(alarm).

% Also ask for the probability John/Mary would call (given the evidence)
query(johnCalls).
query(maryCalls).
