# Structured route results

Use calculate_route(plan, repository, config) from route_service. It returns a JSON-compatible dictionary with timezone, feasible status, numeric OR-Tools solver status, ordered visits and totals. Each visit includes role, expanded node index, destination ID (null for endpoints), display name, original and provider-resolved location, provider IDs, ISO timestamps with timezone offsets, and integer travel, waiting and service seconds.

Travel is inbound to the visit. Arrival assumes immediate departure from the preceding visit; solver slack is reported as waiting at the next location. Service start is the concrete solver assignment. Totals cover the interval from first service start to final departure, including endpoint service. The solver minimizes time variables during finalization to obtain a concrete schedule, not a globally minimum-wait schedule. A feasible result is not a claim of optimality. NoRouteFoundError carries the raw solver status when no solution is found; validation and provider errors remain separate.

The existing cost interface provides durations only; distances are not fabricated. Resolved locations retain provider-specific representation pending canonical coordinates. Travel costs use the existing matrix departure-time assumption. Render separately with render_route(result, config); external renderers may recalculate routes. Named external map links remain deferred. Alternative opening windows are not skipped destinations.

The transitional CLI prints the structured JSON and existing renderer output. No new CLI arguments are required.


## Optional visits

Plan entries may specify required: false and priority: 1 through 5 (default 3). Mandatory is the default; priority is only valid for optional visits. Priorities map to omission penalties of 30, 60, 90, 120 and 150 minutes of objective cost. The objective minimizes travel plus service duration and penalties for solver-omitted visits; waiting is not an objective cost. Priorities are soft trade-offs, not strict rankings. All opening-window alternatives of an optional visit share one penalty and at most one may be selected.

Optional visits with no fitting opening window are omitted before provider requests. Invalid or missing destination data still fails validation, including for optional visits. Provider failures are not silently treated as omissions. Results include visit_index (zero-based input stop index, null for endpoints), required, priority, objective and omitted_visits. Omission reasons distinguish no_fitting_opening_window from not_selected_by_solver; the latter does not prove infeasibility. The objective excludes penalties for visits omitted during preprocessing and is not directly comparable across dates with different available visits. Date-range optimization must account for those omissions separately.
