# Tiger Style

Use [Tiger Style](https://tigerstyle.dev/) to prioritize safety, performance and
developer experience, in that order.

* Set explicit limits on bytes, work items, queues, concurrent operations,
  retries and elapsed time where those resources can grow. Derive limits from
  provider contracts or representative workloads. Define what happens at the
  limit, and require progress in pagination and other repeated work.
* Validate external data before expensive work or state changes. Encode
  invariants in types where practical and use assertions for programmer errors.
  Handle operating failures explicitly, including the effects of cancellation,
  retries and partial writes. Check persisted data when reading it back.
* Keep control flow and state transitions easy to trace. Prefer direct data
  flow, small interfaces and existing dependencies that meet the contract.
  Exercise the limit, the first rejected value and relevant failure paths.
* Estimate the dominant network, storage, memory and CPU costs. Batch work
  where fixed costs dominate and reuse data already fetched or parsed. Verify
  performance claims on representative optimized builds and follow the
  [performance scout guidance](performance-scout.md) where applicable.
* Follow the language and repository conventions. Use fixed-width values when
  an interface requires exact widths, and choose allocation and data layout
  based on the runtime's needs and measurements.

See the [TigerBeetle guide](https://github.com/tigerbeetle/tigerbeetle/blob/main/docs/TIGER_STYLE.md)
for detailed rationale.
