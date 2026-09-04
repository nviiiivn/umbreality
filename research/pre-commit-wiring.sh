#!/bin/sh
# Nothing new may be written that nothing calls.
#
# This world grew by adding modules rather than by extending the one loop
# that runs them, so features arrived finished and dead: the wardens never
# patrolled, the pilgrimage was never required, apply_reality_shift was never
# invoked, sim/strategies.py was never imported, and gnu.cycle - which says
# "safe on a timer" in its own docstring - was never put on one. Nothing
# failed. Nothing errored. They sat there looking done.
#
# research/wiring.py walks the call graph out from the things that actually
# run - the scheduler, the HTTP routes, a spark's turn - and refuses a commit
# that increases the number of functions nothing can reach.
#
# If this stops you: wire it to the scheduler, give it a route, call it from
# a spark's turn, or delete it. Do not raise the budget to make it pass.
python3 research/wiring.py > /tmp/umb-wiring.txt 2>&1
rc=$?
if [ "$rc" -ne 0 ]; then
  echo
  cat /tmp/umb-wiring.txt
  echo
  echo "Commit refused: something was written that nothing reaches."
  exit 1
fi
tail -2 /tmp/umb-wiring.txt
exit 0
